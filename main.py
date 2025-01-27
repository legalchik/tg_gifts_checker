from pyrogram import Client, types
from pyrogram.errors import exceptions
from io import BytesIO
from pytz import timezone as _timezone

import json
import math
import asyncio
import typing

import utils
import config


timezone = _timezone(config.TIMEZONE)

null_str: str = ""


async def detector(app: Client, new_callback: typing.Callable, update_callback: typing.Callable, connect_every_loop: bool=True) -> None:
    while True:
        print("Checking...")

        if not app.is_connected:
            await app.start()

        old_star_gifts_raw: list[dict]

        try:
            with config.DATA_FILEPATH.open("r") as file:
                old_star_gifts_raw = json.load(file)

        except FileNotFoundError:
            old_star_gifts_raw = []

        old_star_gifts_raw_dict: dict[int, dict] = {
            star_gift_raw["id"]: star_gift_raw
            for star_gift_raw in old_star_gifts_raw
        }

        all_star_gifts_raw: list[dict] = [
            json.loads(json.dumps(
                star_gift,
                indent = 4,
                default = types.Object.default,
                ensure_ascii = False
            ))
            for star_gift in await app.get_star_gifts()
        ]

        all_star_gifts_raw_dict: dict[int, dict] = {
            star_gifts_raw["id"]: star_gifts_raw
            for star_gifts_raw in all_star_gifts_raw
        }

        new_star_gifts_raw: dict[int, dict] = {
            key: value
            for key, value in all_star_gifts_raw_dict.items()
            if key not in old_star_gifts_raw_dict
        }

        all_star_gifts_ids: list[int] = list(all_star_gifts_raw_dict.keys())
        all_star_gifts_amount: int = len(all_star_gifts_ids)

        if new_star_gifts_raw:
            print("New star gifts found:", len(new_star_gifts_raw))

            for star_gift_id, star_gift_raw in new_star_gifts_raw.items():
                star_gift_raw["number"] = all_star_gifts_amount - all_star_gifts_ids.index(star_gift_id)

            for star_gift_id, star_gift_raw in sorted(
                new_star_gifts_raw.items(),
                key = lambda it: it[1]["number"]
            ):
                await new_callback(
                    app,
                    star_gift_raw
                )

        if update_callback:
            for star_gift_id, old_star_gift_raw in old_star_gifts_raw_dict.items():
                new_star_gift_raw: dict = all_star_gifts_raw_dict[star_gift_id]
                old_available_amount: int = old_star_gift_raw.get("available_amount", -1)

                if "message_id" in old_star_gift_raw:
                    new_star_gift_raw["message_id"] = old_star_gift_raw["message_id"]

                new_star_gift_raw["number"] = all_star_gifts_amount - all_star_gifts_ids.index(star_gift_id)

                if old_available_amount > -1 and new_star_gift_raw["available_amount"] < old_available_amount:
                    await update_callback(
                        app,
                        old_star_gift_raw,
                        new_star_gift_raw
                    )

        with config.DATA_FILEPATH.open("w") as file:
            json.dump(
                obj = all_star_gifts_raw,
                fp = file,
                indent = 4,
                default = types.Object.default,
                ensure_ascii = False
            )

        if connect_every_loop:
            await app.stop()

        await asyncio.sleep(config.CHECK_INTERVAL)


def get_notify_text(star_gift_raw: dict) -> str:
    is_limited: bool = star_gift_raw["is_limited"]

    if is_limited:
        available_percentage, available_percentage_is_same = utils.pretty_float(
            number = math.ceil(star_gift_raw["available_amount"] / star_gift_raw["total_amount"] * 100 * 100) / 100,
            get_is_same = True
        )

    return config.NOTIFY_TEXT.format(
        title = config.NOTIFY_TEXT_TITLES[is_limited],
        number = star_gift_raw.pop("number"),
        id = star_gift_raw["id"],
        total_amount = (
            config.NOTIFY_TEXT_TOTAL_AMOUNT.format(
                total_amount = utils.pretty_int(star_gift_raw["total_amount"])
            )
            if is_limited
            else
            null_str
        ),
        available_amount = (
            config.NOTIFY_TEXT_AVAILABLE_AMOUNT.format(
                available_amount = utils.pretty_int(star_gift_raw["available_amount"]),
                same_str = (
                    null_str
                    if available_percentage_is_same
                    else
                    "~"
                ),
                available_percentage = available_percentage,
                updated_datetime = utils.get_current_datetime(timezone)
            )
            if is_limited
            else
            null_str
        ),
        price = utils.pretty_int(star_gift_raw["price"]),
        convert_price = utils.pretty_int(star_gift_raw["convert_price"])
    )


async def new_callback(app: Client, star_gift_raw: dict) -> None:
    binary: BytesIO = await app.download_media(
        message = star_gift_raw["sticker"]["file_id"],
        in_memory = True
    )

    binary.name = "{}.{}".format(
        star_gift_raw["id"],
        star_gift_raw["sticker"]["file_name"].split(".")[-1]
    )

    sticker_message: types.Message = await app.send_sticker(
        chat_id = config.NOTIFY_CHAT_ID,
        sticker = binary
    )

    await asyncio.sleep(config.NOTIFY_AFTER_STICKER_DELAY)

    message: types.Message = await app.send_message(
        chat_id = config.NOTIFY_CHAT_ID,
        text = get_notify_text(star_gift_raw),
        reply_to_message_id = sticker_message.id
    )

    star_gift_raw["message_id"] = message.id

    await asyncio.sleep(config.NOTIFY_AFTER_TEXT_DELAY)


async def update_callback(app: Client, old_star_gift_raw: dict, new_star_gift_raw: dict) -> None:
    if "message_id" not in new_star_gift_raw:
        return

    try:
        await app.edit_message_text(
            chat_id = config.NOTIFY_CHAT_ID,
            text = get_notify_text(new_star_gift_raw),
            message_id = new_star_gift_raw["message_id"]
        )

    except exceptions.MessageNotModified:
        pass

    await asyncio.sleep(config.NOTIFY_AFTER_TEXT_DELAY)


async def main() -> None:
    app: Client = Client(
        name = config.SESSION_NAME,
        api_id = config.API_ID,
        api_hash = config.API_HASH
    )

    await detector(
        app = app,
        new_callback = new_callback,
        update_callback = update_callback
    )


if __name__ == "__main__":
    asyncio.run(main())
