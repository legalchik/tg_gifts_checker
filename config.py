from pathlib import Path


API_ID: int = 1234
API_HASH: str = "1234"
NOTIFY_CHAT_ID: int = -1002452845734


CHECK_INTERVAL: float = 90.

SESSION_NAME: str = "account"

DATA_FILEPATH: Path = Path(__file__).parent / "star_gifts.json"
NOTIFY_AFTER_STICKER_DELAY: float = 1.
NOTIFY_AFTER_TEXT_DELAY: float = 2.
TIMEZONE: str = "UTC"


NOTIFY_TEXT: str = """\
{title}

№ {number} (<code>{id}</code>)
{total_amount}{available_amount}
💎 Price: {price} ⭐️
♻️ Convert price: {convert_price} ⭐️
"""

NOTIFY_TEXT_TITLES: dict[bool, str] = {
    True: "🔥 A new limited gift has appeared",
    False: "❄️ A new gift has appeared"
}

NOTIFY_TEXT_TOTAL_AMOUNT: str = "\n🎯 Total amount: {total_amount}"
NOTIFY_TEXT_AVAILABLE_AMOUNT: str = "\n❓ Available amount: {available_amount} ({same_str}{available_percentage}%, updated at {updated_datetime} UTC)\n"
