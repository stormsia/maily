import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from mailtmapi import MailClient
from mailtmapi.core.client import MailClient
from mailtmapi.providers.mailtm import MailTMProvider
from mailtmapi.providers.tempmail_plus import TempMailPlusProvider


async def async_input(prompt: str) -> str:
    print(prompt, end="", flush=True)
    return await asyncio.to_thread(sys.stdin.readline)


async def test_provider(client: MailClient, provider_name: str):
    print(f"\n{'=' * 50}")
    print(f"Testing provider: {provider_name}")
    print(f"{'=' * 50}")

    # 1. Get all domains
    print("\n[1] Fetching domains...")
    domains = await client.get_all_domains(provider=provider_name)
    print(f"  -> Found {len(domains)} domains for {provider_name}.")
    if not domains:
        print("  -> No domains found, skipping...")
        return
    print(f"  -> First domain: {domains[0]['domain']}")

    # 2. Create account
    print("\n[2] Creating an account...")
    account = await client.create_account(provider=provider_name)
    print(f"  -> Account created successfully!")
    print(f"  -> ID: {account.api_id}")
    print(f"  -> Address: {account.address}")
    print(f"  -> Password: {account.password}")

    # 3. Wait for message
    print(f"\n[3] Waiting for an email to be received...")
    print(f"*** PLEASE SEND AN EMAIL TO: {account.address} ***")
    
    # We use a custom wait loop or wait_for_messages
    print("  -> Waiting for up to 5 minutes...")
    messages = await client.wait_for_messages(account.id, timeout=300.0, check_interval=5.0)
    
    if not messages:
        print("  -> No messages received within the timeout.")
        return
    
    msg = messages[0]
    print(f"  -> Message received! ID: {msg.message_api_id}")
    print(f"  -> From: {msg.from_address} ({msg.from_name})")
    print(f"  -> Subject: {msg.subject}")

    # 4. Get Message Detail & Cache
    print("\n[4] Fetching message detail & caching body...")
    cached_msg = await client.cache_message_body(account.id, msg.message_api_id)
    print(f"  -> Cached! Text body length: {len(cached_msg.body_text or '')}")
    if cached_msg.body_html:
        print(f"  -> Cached! HTML body length: {len(cached_msg.body_html)}")

    # 5. Mark as read
    print("\n[5] Marking message as read...")
    read_success = await client.mark_message_as_read(msg.message_api_id, account.id)
    print(f"  -> Success: {read_success}")

    # 6. Provider specific methods (get_message_source, get_me, get_account_by_id, delete_message)
    print("\n[6] Testing provider-specific direct API methods...")
    prov = client._get_provider(provider_name)
    
    try:
        me = await prov.get_me(account.token)
        print(f"  -> get_me(): quota={me.quota}, used={me.used}")
    except Exception as e:
        print(f"  -> get_me() error (might not be supported): {e}")

    try:
        acc_info = await prov.get_account_by_id(account.api_id, account.token)
        print(f"  -> get_account_by_id(): address={acc_info.address}")
    except Exception as e:
        print(f"  -> get_account_by_id() error (might not be supported): {e}")

    try:
        source = await prov.get_message_source(msg.message_api_id, account.token)
        print(f"  -> get_message_source(): url={source.downloadUrl}, data_len={len(source.data or '')}")
    except Exception as e:
        print(f"  -> get_message_source() error (might not be supported): {e}")

    try:
        print(f"  -> Deleting message: {msg.message_api_id}")
        del_msg_success = await prov.delete_message(msg.message_api_id, account.token)
        print(f"  -> delete_message(): {del_msg_success}")
    except Exception as e:
        print(f"  -> delete_message() error: {e}")

    # 7. Delete account
    print("\n[7] Deleting account...")
    del_acc_success = await client.delete_account(account.id)
    print(f"  -> Success: {del_acc_success}")


async def main():
    print("Initializing MailClient...")
    # Use :memory: db for testing so we don't leave garbage
    async with MailClient(db_path="example_demo1.db") as client:
        # account = await client.create_account(domain="mailto.plus")
        # print(account)
        # return
        # confirmation = await client.wait_for_confirmation_email(
        #     2,
        #     sender_domain="mailto.plus",
        #     # url_contain=["111"],
        #     digit_code_mask=r"\b\d{6}\b",
        #     timeout=150,
        #     check_interval=3,
        # )
        # print(confirmation)
        # return
        providers = ["mail.tm", "tempmail.plus"]
        
        print("\nLoaded providers:")
        for p in client.providers:
            print(f" - {p.provider_name}")

        for provider_name in providers:
            await test_provider(client, provider_name)
            
            resp = await async_input("\nContinue to the next provider? (Y/n): ")
            if resp.strip().lower() == 'n':
                break

    print("\nAll tests completed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted.")
