"""
Example: multi-provider MailClient.

Demonstrates:
  - Listing all domains across all providers
  - Creating accounts on different providers
  - Fetching and reading messages (including body caching)
  - Managing accounts in the local database
  - Cleaning up

Run::
    python example_client.py
"""
import asyncio
import logging
import sys
import os

# Ensure the local package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mailtmapi import MailClient

# Set up logging to see what the library is doing under the hood
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S"
)

async def main() -> None:
    # Initialize MailClient with an SQLite database to store accounts and messages
    async with MailClient(db_path="example_demo.db") as client:
        # ── 1. List Domains ────────────────────────────────────────────────
        print("\n=== 🌐 Available Domains ===")
        domains = await client.get_all_domains()
        for d in domains:  # Show just the first 5 to avoid spam
            print(f"  • {d['domain']} [Provider: {d['provider']}]")
        

        # ── 2. Create Accounts ─────────────────────────────────────────────
        print("\n=== 👤 Creating Accounts ===")
        
        # Create an account on mail.tm
        print("Creating account on mail.tm...")
        acc_tm = await client.create_account(provider="mail.tm")
        print(f"  ✅ Created: {acc_tm.address} (DB ID: {acc_tm.id})")
        
        # Create an account on tempmail.plus
        print("Creating account on tempmail.plus...")
        acc_tmp = await client.create_account(provider="tempmail.plus")
        print(f"  ✅ Created: {acc_tmp.address} (DB ID: {acc_tmp.id})")

        # ── 3. Check Messages ──────────────────────────────────────────────
        print(f"\n=== 📥 Checking Inbox for {acc_tm.address} ===")
        
        # Give mail.tm a moment to deliver its standard welcome email
        await asyncio.sleep(2)
        
        messages = await client.get_messages(acc_tm.id)
        print(f"  Found {len(messages)} message(s).")
        
        for msg in messages:
            print(f"\n  ✉️  Subject: {msg.subject}")
            print(f"      From:    {msg.from_name} <{msg.from_address}>")
            print(f"      Date:    {msg.received_at}")
            
            # Download the full body (HTML/Text) and save it to the DB
            print("      [Downloading message body...]")
            full_msg = await client.cache_message_body(acc_tm.id, msg.message_api_id)
            
            if full_msg.body_text:
                preview = full_msg.body_text.strip().replace('\n', ' ')[:100]
                print(f"      Preview: {preview}...")

        # ── 4. Wait for Specific Email (Polling) ───────────────────────────
        print(f"\n=== ⏳ Waiting for email for {acc_tm.address} (timeout 15s) ===")
        print("  (This will time out unless you actually send an email to that address)")
        confirmation = await client.wait_for_confirmation_email(
            acc_tm.id,
            sender_domain="gmail.com",
            timeout=150,
            check_interval=3,
        )
        if confirmation:
            print(f"  ✅ Received! From: {confirmation['from_address']}")
            print(f"      Link: {confirmation['confirmation_link']}")
            await client.mark_message_as_read(confirmation["message_id"], acc_tm.id)
        else:
            print("  ⏱️  Timed out waiting for confirmation email.")

        # ── 5. Local Database Accounts ─────────────────────────────────────
        print("\n=== 🗃️  Local Database Overview ===")
        all_accounts = client.get_all_accounts()
        print(f"  Total accounts in DB: {len(all_accounts)}")
        
        # Show just the last 3 created accounts to keep it tidy
        for acc in all_accounts[-3:]:
            unread = client.get_unread_count(acc.id)
            status = "🟢 Active" if acc.is_active else "🔴 Deleted"
            print(f"  • {acc.address:30s} | {status} | Unread: {unread}")

        # ── 6. Cleanup ─────────────────────────────────────────────────────
        print("\n=== 🧹 Cleaning up ===")
        for acc in [acc_tm, acc_tmp]:
            print(f"Deleting {acc.address}...")
            success = await client.delete_account(acc.id)
            if success:
                print("  ✅ Deleted successfully.")
            else:
                print("  ❌ Failed to delete.")

    print("\n✨ Done! Example finished successfully.")

if __name__ == "__main__":
    asyncio.run(main())
