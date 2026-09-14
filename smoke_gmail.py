"""Smoke test: GmailProvider OAuth login + alias creation."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mailtmapi.providers.gmail import GmailProvider


async def main() -> None:
    prov = GmailProvider(
        credentials_path=r"C:\Users\sia\Desktop\github_account_creator\mailtmapi\credentials.json"
    )
    try:
        acc = await prov.create_account()
        print("LOGIN OK + alias created:", acc.address)
        me = await prov.get_me(acc.token.token)
        print("Profile email:", me.address)
        bases = await prov._get_base_addresses()
        print("Base addresses (profile + your sendAs aliases):", bases)

        # create 5 aliases round-robin
        for _ in range(5):
            a = await prov.create_account()
            print("alias:", a.address)
    finally:
        await prov.close()


asyncio.run(main())