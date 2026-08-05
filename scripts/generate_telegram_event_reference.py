#!/usr/bin/env python3
"""Generate the Telegram system-event reference tables from the official clients.

Telegram records system events (calls, screenshots, membership changes, timer
changes) as message actions. iOS and Android name the same event differently and
version them differently, so the tables below are extracted from each client's
own source rather than retyped, and the cross-platform pairing is applied from a
reviewed map kept in this file.

The event lists go stale: iLEAPP's copy of the iOS list sat twenty entries
behind before this work. Re-run this whenever the reference is refreshed.

Usage:
    python3 scripts/generate_telegram_event_reference.py            # write tables
    python3 scripts/generate_telegram_event_reference.py --check    # report drift only

Requires the `gh` CLI, authenticated, for the two source fetches.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

IOS_REPO = 'TelegramMessenger/Telegram-iOS'
IOS_PATH = ('submodules/TelegramCore/Sources/SyncCore/'
            'SyncCore_TelegramMediaAction.swift')
ANDROID_REPO = 'DrKLO/Telegram'
ANDROID_PATH = ('TMessagesProj_AppTests/src/androidTest/kotlin/org/telegram/tgnet/'
                'model/generated/TlGen_MessageAction.kt')
IOS_SOURCE = f'repos/{IOS_REPO}/contents/{IOS_PATH}'
ANDROID_SOURCE = f'repos/{ANDROID_REPO}/contents/{ANDROID_PATH}'

# Events whose iOS and Android names differ. Reviewed by hand: string matching
# pairs only 27 of roughly seventy concepts, because the clients name the same
# event differently (iOS addedMembers is Android ChatAddUser, and so on).
CROSS_MAP = {
    'addedMembers': 'ChatAddUser',
    'removedMembers': 'ChatDeleteUser',
    'photoUpdated': 'ChatEditPhoto',
    'titleUpdated': 'ChatEditTitle',
    'pinnedMessageUpdated': 'PinMessage',
    'joinedByLink': 'ChatJoinedByLink',
    'joinedByRequest': 'ChatJoinedByRequest',
    'groupCreated': 'ChatCreate',
    'channelMigratedFromGroup': 'ChannelMigrateFrom',
    'groupMigratedToChannel': 'ChatMigrateTo',
    'historyCleared': 'HistoryClear',
    'historyScreenshot': 'ScreenshotTaken',
    'messageAutoremoveTimeoutUpdated': 'SetMessagesTTL',
    'phoneCall': 'PhoneCall',
    'groupPhoneCall': 'GroupCall',
    'inviteToGroupPhoneCall': 'InviteToGroupCall',
    'conferenceCall': 'ConferenceCall',
    'geoProximityReached': 'GeoProximityReached',
    'peerJoined': 'ContactSignUp',
    'customText': 'CustomAction',
    'gameScore': 'GameScore',
    'paymentSent': 'PaymentSent',
    'paymentRefunded': 'PaymentRefunded',
    'botSentSecureValues': 'SecureValuesSent',
    'botDomainAccessGranted': 'BotAllowed',
    'botAppAccessGranted': 'BotAllowed',
    'attachMenuBotAllowed': 'AttachMenuBotAllowed',
    'webViewData': 'WebViewDataSent',
    'suggestedProfilePhoto': 'SuggestProfilePhoto',
    'suggestedBirthday': 'SuggestBirthday',
    'setChatTheme': 'SetChatTheme',
    'setChatWallpaper': 'SetChatWallPaper',
    'setSameChatWallpaper': 'SetSameChatWallPaper',
    'topicCreated': 'TopicCreate',
    'topicEdited': 'TopicEdit',
    'giftPremium': 'GiftPremium',
    'giftCode': 'GiftCode',
    'giftStars': 'GiftStars',
    'giftTon': 'GiftTon',
    'prizeStars': 'PrizeStars',
    'starGift': 'StarGift',
    'starGiftUnique': 'StarGiftUnique',
    'starGiftPurchaseOffer': 'StarGiftPurchaseOffer',
    'starGiftPurchaseOfferDeclined': 'StarGiftPurchaseOfferDeclined',
    'giveawayLaunched': 'GiveawayLaunch',
    'giveawayResults': 'GiveawayResults',
    'boostsApplied': 'BoostApply',
    'requestedPeer': 'RequestedPeer',
    'copyProtectionToggle': 'NoForwardsToggle',
    'copyProtectionRequest': 'NoForwardsRequest',
    'groupCreatorChange': 'ChangeCreator',
    'communityChanged': 'ChangeCommunity',
    'managedBotCreated': 'ManagedBotCreated',
    'pollOptionAppended': 'PollAppendAnswer',
    'pollOptionDeleted': 'PollDeleteAnswer',
    'todoCompletions': 'TodoCompletions',
    'todoAppendTasks': 'TodoAppendTasks',
    'paidMessagesRefunded': 'PaidMessagesRefunded',
    'paidMessagesPriceEdited': 'PaidMessagesPrice',
    'suggestedPostApprovalStatus': 'SuggestedPostApproval',
    'suggestedPostSuccess': 'SuggestedPostSuccess',
    'suggestedPostRefund': 'SuggestedPostRefund',
    'channelCreated': 'ChannelCreate',
    'joinedChannel': 'JoinedChannel',
    'phoneNumberRequest': 'PhoneNumberRequest',
}

# What the event records, in examiner terms. Keyed by the iOS name where one
# exists, otherwise the Android name.
PURPOSE = {
    'groupCreated': 'A basic group was created. Carries the title.',
    'channelCreated': 'A channel or supergroup was created.',
    'addedMembers': 'One or more users were added to the chat.',
    'removedMembers': 'A user was removed from the chat.',
    'photoUpdated': 'The group or channel photo was changed.',
    'titleUpdated': 'The group or channel name was changed.',
    'pinnedMessageUpdated': 'A message was pinned in the chat.',
    'joinedByLink': 'A user joined via an invite link. Names the inviter.',
    'joinedByRequest': 'A user joined after an admin approved their request.',
    'channelMigratedFromGroup': 'This channel was converted from a basic group.',
    'groupMigratedToChannel': 'This group was upgraded to a supergroup.',
    'historyCleared': 'The chat history was cleared.',
    'historyScreenshot': 'A screenshot was taken in a secret chat.',
    'messageAutoremoveTimeoutUpdated': 'The auto-delete timer was changed. Carries the new value.',
    'phoneCall': 'A one-to-one voice or video call. Carries call id, outcome and duration.',
    'groupPhoneCall': 'A group voice chat. Carries the call id and duration.',
    'groupCallScheduled': 'A group call was scheduled for a future time.',
    'inviteToGroupPhoneCall': 'Users were invited to a group call.',
    'conferenceCall': 'A conference call. Carries duration and participants.',
    'geoProximityReached': 'A proximity alert fired. Carries the distance in metres.',
    'peerJoined': 'A contact from the address book joined Telegram.',
    'customText': 'A server-supplied notice rendered as text.',
    'gameScore': 'A score was posted in a bot game.',
    'paymentSent': 'A payment was completed. Carries currency and amount.',
    'paymentRefunded': 'A payment was refunded.',
    'botSentSecureValues': 'Telegram Passport data was shared with a bot.',
    'botDomainAccessGranted': 'The user granted a website access via the bot login.',
    'botAppAccessGranted': 'The user granted a bot mini app access.',
    'attachMenuBotAllowed': 'A bot was added to the attachment menu.',
    'webViewData': 'Data was submitted from a bot web view.',
    'suggestedProfilePhoto': 'A profile photo was suggested to the user.',
    'suggestedBirthday': 'A birthday was suggested to the user.',
    'setChatTheme': 'The chat theme was changed.',
    'setChatWallpaper': 'The chat wallpaper was changed.',
    'setSameChatWallpaper': 'The peer applied the same wallpaper.',
    'topicCreated': 'A forum topic was created.',
    'topicEdited': 'A forum topic was renamed or reconfigured.',
    'requestedPeer': 'The user shared a peer with a bot on request.',
    'copyProtectionToggle': 'Content protection (restrict saving) was switched.',
    'copyProtectionRequest': 'Content protection was requested.',
    'groupCreatorChange': 'Chat ownership was transferred.',
    'communityChanged': 'The chat was moved into or out of a community.',
    'managedBotCreated': 'A managed bot was created for the chat.',
    'pollOptionAppended': 'An option was added to a poll.',
    'pollOptionDeleted': 'An option was removed from a poll.',
    'todoCompletions': 'To-do items were marked complete or incomplete.',
    'todoAppendTasks': 'Tasks were appended to a to-do list.',
    'joinedChannel': 'The user joined the channel.',
    'phoneNumberRequest': 'A bot requested the user phone number.',
    'giftPremium': 'A Telegram Premium subscription was gifted.',
    'giftCode': 'A Premium gift code was issued.',
    'giftStars': 'Telegram Stars were gifted.',
    'giftTon': 'TON was gifted.',
    'prizeStars': 'Stars were awarded as a giveaway prize.',
    'starGift': 'A star gift was sent.',
    'starGiftUnique': 'A unique (collectible) star gift changed hands.',
    'starGiftPurchaseOffer': 'An offer was made to purchase a star gift.',
    'starGiftPurchaseOfferDeclined': 'A star gift purchase offer was declined.',
    'giveawayLaunched': 'A giveaway was started in the channel.',
    'giveawayResults': 'Giveaway results were published.',
    'boostsApplied': 'Channel boosts were applied.',
    'paidMessagesRefunded': 'Paid messages were refunded.',
    'paidMessagesPriceEdited': 'The price for paid messages was changed.',
    'suggestedPostApprovalStatus': 'A suggested post was approved or rejected.',
    'suggestedPostSuccess': 'A suggested post was published successfully.',
    'suggestedPostRefund': 'A suggested post payment was refunded.',
    'unknown': 'An action the client could not interpret.',
    'Empty': 'A placeholder action with no content.',
    'GroupCallScheduled': 'A group call was scheduled for a future time.',
    'ChatDeletePhoto': 'The group or channel photo was removed.',
    'ChannelCreate': 'A channel was created. Carries the title.',
    'NewCreatorPending': 'A transfer of chat ownership is pending confirmation.',
    'PaymentSentMe': 'Bot-side record of a payment received from a user.',
    'WebViewDataSentMe': 'Bot-side record of data submitted from a web view.',
}

# Events whose payload fields the LEAPPs parsers decode and report.
IOS_PAYLOAD = {
    'phoneCall', 'groupPhoneCall', 'conferenceCall', 'messageAutoremoveTimeoutUpdated',
    'geoProximityReached', 'gameScore', 'groupCreated', 'titleUpdated', 'customText',
    'joinedByLink', 'paymentSent', 'addedMembers', 'removedMembers', 'suggestedBirthday',
    'copyProtectionToggle', 'managedBotCreated',
}
ANDROID_PAYLOAD = {
    'PhoneCall', 'SetMessagesTTL', 'ChatCreate', 'ChatEditTitle', 'ChatAddUser',
    'ChatDeleteUser', 'ChatJoinedByLink', 'InviteToGroupCall', 'GeoProximityReached',
    'GameScore', 'CustomAction', 'PaymentSent',
}


def fetch(api_path: str) -> str:
    result = subprocess.run(['gh', 'api', api_path, '--jq', '.content'],
                            capture_output=True, text=True, check=True)
    return base64.b64decode(result.stdout).decode('utf-8', 'replace')


def head_sha(repo: str, path: str) -> str:
    """Commit that last touched the file.

    Permalinks are pinned to a commit rather than to main on purpose: line
    numbers move with every upstream edit, and a link to main would silently
    start pointing at the wrong line.
    """
    result = subprocess.run(
        ['gh', 'api', f'repos/{repo}/commits?path={path}&per_page=1', '--jq', '.[0].sha'],
        capture_output=True, text=True, check=True)
    return result.stdout.strip()


def permalink(repo: str, sha: str, path: str, line: int) -> str:
    return f'https://github.com/{repo}/blob/{sha}/{path}#L{line}'


def parse_ios(source: str) -> dict[str, tuple[int, int]]:
    """iOS stores an ordinal discriminator, written in the encode switch.

    Returns name -> (rawValue, line number of the case that defines it).
    """
    actions, current, case_line = {}, None, 0
    for number, line in enumerate(source.splitlines(), start=1):
        match = re.match(r'\s*case (?:let )?\.(\w+)', line)
        if match:
            current, case_line = match.group(1), number
        raw = re.search(r'encodeInt32\((\d+), forKey: "_rawValue"\)', line)
        if raw and current:
            actions[current] = (int(raw.group(1)), case_line)
            current = None
    return actions


def parse_android(source: str) -> dict[str, dict]:
    """Android keys on constructor hashes, one per layer version of an event.

    Returns family -> {ctors: [...], line: declaration line of the newest one}.
    """
    actions, current, class_line = {}, None, 0
    for number, line in enumerate(source.splitlines(), start=1):
        match = re.search(r'public (?:data )?(?:class|object) (TL_\w+)', line)
        if match:
            current, class_line = match.group(1), number
        magic = re.search(r'MAGIC: UInt = (0x[0-9A-Fa-f]+)U', line)
        if magic and current:
            family = re.sub(r'_layer\d+$', '', current).replace('TL_messageAction', '')
            entry = actions.setdefault(family, {'ctors': [], 'line': class_line})
            entry['ctors'].append(magic.group(1).lower())
            current = None
    return actions


def build_rows(ios: dict, android: dict, ios_sha: str, android_sha: str) -> list[dict]:
    paired_android = set()
    rows = []
    for name, (raw, line) in sorted(ios.items(), key=lambda item: item[1][0]):
        counterpart = CROSS_MAP.get(name)
        if counterpart not in android:
            counterpart = name if name in android else None
        if counterpart:
            paired_android.add(counterpart)
        entry = android.get(counterpart) if counterpart else None
        rows.append({
            'ios': name,
            'ios_raw': raw,
            'ios_url': permalink(IOS_REPO, ios_sha, IOS_PATH, line),
            'android': counterpart or '',
            'android_ctors': entry['ctors'] if entry else [],
            'android_url': (permalink(ANDROID_REPO, android_sha, ANDROID_PATH, entry['line'])
                            if entry else ''),
            'purpose': PURPOSE.get(name, ''),
            'payload': ('iOS' if name in IOS_PAYLOAD else '')
                       + ('/' if name in IOS_PAYLOAD and counterpart in ANDROID_PAYLOAD else '')
                       + ('Android' if counterpart in ANDROID_PAYLOAD else ''),
        })
    for name in sorted(android):
        if name in paired_android:
            continue
        entry = android[name]
        rows.append({
            'ios': '', 'ios_raw': None, 'ios_url': '',
            'android': name,
            'android_ctors': entry['ctors'],
            'android_url': permalink(ANDROID_REPO, android_sha, ANDROID_PATH, entry['line']),
            'purpose': PURPOSE.get(name, ''),
            'payload': 'Android' if name in ANDROID_PAYLOAD else '',
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true',
                        help='report counts and unmapped names, write nothing')
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'scripts' / 'data' / 'telegram-events.json')
    args = parser.parse_args()

    ios_sha = head_sha(IOS_REPO, IOS_PATH)
    android_sha = head_sha(ANDROID_REPO, ANDROID_PATH)
    ios = parse_ios(fetch(IOS_SOURCE))
    android = parse_android(fetch(ANDROID_SOURCE))
    rows = build_rows(ios, android, ios_sha, android_sha)

    both = [r for r in rows if r['ios'] and r['android']]
    ios_only = [r for r in rows if r['ios'] and not r['android']]
    android_only = [r for r in rows if not r['ios']]
    missing_purpose = [r for r in rows if not r['purpose']]

    print(f'iOS source pinned at   {ios_sha[:12]}')
    print(f'Android source pinned at {android_sha[:12]}')
    print(f'iOS actions:      {len(ios)} '
          f'(max rawValue {max(v[0] for v in ios.values())})')
    print(f'Android events:   {len(android)} families, '
          f'{sum(len(v["ctors"]) for v in android.values())} constructors')
    print(f'paired:           {len(both)}')
    print(f'iOS only:         {len(ios_only)} {[r["ios"] for r in ios_only]}')
    print(f'Android only:     {len(android_only)} {[r["android"] for r in android_only]}')
    if missing_purpose:
        print(f'NO PURPOSE TEXT:  {len(missing_purpose)} '
              f'{[r["ios"] or r["android"] for r in missing_purpose]}')

    if args.check:
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(
        {'ios_sha': ios_sha, 'android_sha': android_sha, 'events': rows},
        indent=1) + '\n')
    print(f'Wrote {args.output.relative_to(ROOT)} ({len(rows)} rows)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
