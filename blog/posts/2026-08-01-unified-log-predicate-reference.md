---
title: "Apple Unified Log Predicates in iLEAPP: The Reference"
date: 2026-08-01
author: Alexis Brignoni
tags: [iLEAPP, iOS, Unified Logs, LAVA, DFIR, Reference]
excerpt: Every Unified Log message predicate iLEAPP searches for, artifact by artifact, with the processes involved, the iOS versions each pattern was observed on, the sources that documented them, and the caveats that keep you honest.
---

# Apple Unified Log Predicates in iLEAPP: The Reference

This is the companion to the [Unified Logs workflow guide](https://www.leapps.org/blog-post?post=2026-07-29-apple-unified-logs). That article covers how to acquire, preserve, and process the logs. This one answers the question that comes right after processing: what exactly is iLEAPP looking for, and why should you trust any of it?

As of iLEAPP's main branch on August 1, 2026, the Unified Logs module registers **34 artifacts** driven by **230 unique message predicates**. Every single one of them meets a standard I want to be transparent about, because nobody should take "the tool found it" as an answer:

1. **Documented**: the pattern comes from published research that was fetched and verified, not from memory or folklore. The source is cited on the artifact, in the code, and here.
2. **Observed**: the pattern was matched against real full file system extractions. Three images did the heavy lifting: an iPhone 8 Plus on iOS 16.5 (19.4 million log records), an iPhone 11 Pro on iOS 17.1 (30.4 million records), and an iPhone 12 on iOS 18.7 (20.5 million records).

Most patterns meet both bars. Where a pattern is documented but the event never occurred in our images, the artifact notes say **documented-only**, and so does this guide. An empty artifact is not evidence of absence, and a populated one still deserves validation on your device and iOS version before it goes in a report.

Three caveats apply to everything below, so I will say them once instead of two hundred and thirty times:

- **Payloads redact.** On production devices the dynamic values in many messages render as `<private>`. The predicates anchor on the static message text on purpose. When a value does survive in the clear, treasure it.
- **Strings drift.** Apple changes log messages between iOS versions. We already carry version-specific variants for several patterns, and iOS 26 changed others. A miss on your image may just mean a new spelling nobody has documented yet.
- **Retention is short and uneven.** Most entries live hours to days, not the mythical 30. Tim Korver and Lionel Notari have both published on this. Acquire early.

The verbatim, always-current predicate list lives in the [iLEAPP source module](https://github.com/abrignoni/iLEAPP/blob/main/scripts/artifacts/logarchive.py). The lists below were generated from that file, not retyped, which is the only honest way to publish two hundred plus strings.

## How the module is put together

Two artifacts do the heavy lifting, and everything else filters their output:

- **logarchive** imports every record into the LAVA database. On the iPhone 12 image that is 20.5 million rows. LAVA-only, for obvious reasons.
- **logarchive artifacts** runs all 230 predicates in a single pass over that table and materializes the matches. Also LAVA-only.

The remaining 32 artifacts each carve their slice out of that filtered set. Twenty-nine produce standard reports; the three highest-volume ones (keyboard activity, biometric sensor events, touchscreen events) are LAVA-only because a two-hundred-thousand-row HTML file helps nobody.

Now the reference, grouped by what the evidence speaks to.

## Human presence and handling

### logarchive biometric sensor events
Sensor-level entries from the Face ID and Touch ID stacks: camera frames with face-detected, attention, and glasses flags, face-to-device distance readings, SpringBoard face-in-view notices, and finger-on/finger-off events on home button devices. Sensor entries record what the hardware saw, not an unlock decision; pair them with the lock artifacts. This is the evidence a person cannot anticipate or stage, which is exactly why Tim Korver ranks it so high on evidential strength.
Observed: Face ID families on iOS 17.1 and 18.7 (11,307 PearlCam frames on the iPhone 12 alone); Touch ID finger events on the iOS 16.5 iPhone 8 Plus. Documented-only: the home button press form (iOS 12 era).
Sources: Thesis Friday [#1](https://thesisfriday.com/thesis-friday-1-aul-faceid/), [#12](https://thesisfriday.com/thesis-friday-12-aul-first-glance-at-ios-26/), [#10](https://thesisfriday.com/thesis-friday-10-artefacts-on-a-iphone-6-ios-12-5-7/), [#22](https://thesisfriday.com/thesis-friday-22-reading-the-unified-log-by-evidential-strength-not-by-timestamp/).

**Predicates:**

- `%PearlCamFrameReceived%`
- `%getFaceDetectInfo%`
- `%[User Presence Monitor]%`
- `%kAppleBiometricFinger%`
- `%Home Button Was Pressed%`

### logarchive touchscreen events
Fingers physically on glass: digitizer contact presence per finger, per-app touch statistics windows, touch attention events, and tap-to-wake. The "was the phone being handled at 14:32" artifact.
Observed: iOS 16.5, 17.1, 18.7.
Sources: [Thesis Friday #14](https://thesisfriday.com/thesis-friday-14-aul-touch-events/), [Lionel Notari on touch events](https://www.ios-unifiedlogs.com/news/ios-unified-logs-touching-the-iphone-screen).

**Predicates:**

- `%contact _ presence:%`
- `%touchstats%`
- `%received tapToWake%`
- `%AttentionAwareness.Touch%`

### logarchive pocket state
The front infrared sensor logging when the device is face-down or stowed, and when it comes back out. Directly speaks to "the phone was in my pocket."
Observed: iOS 17.1 and 18.7. The iOS 16.5 iPhone 8 Plus produced none, which fits its older sensor package.
Sources: [Ian Whiffin's Doppler research](https://doubleblak.com/blogPost.php?k=doppler), [Notari's SQL queries post](https://www.ios-unifiedlogs.com/post/ios-unified-logs-parsing-all-my-sql-queries).

**Predicates:**

- `%Doppler in pocket state%`
- `%PocketState changed%`

### logarchive lock status
The original lock artifact: screen lock and unlock, device lock status, and biometric match messages.
Sources: community research consolidated in the module; see the workflow guide.

**Predicates:**

- `%Screen did lock%`
- `%ScreenOn changed%`
- `%Screen shut off%`
- `%screen is locked%`
- `%screen is unlocked%`
- `%Device unlocked%`
- `%Device lock status%`
- `%Biometric match complete%`

### logarchive unlock sessions and method
The newer, sharper companion: session durations ("Was unlocked for N seconds"), authentication requests with type and outcome (type 1 passcode, type 2 biometric, and failures log too), chronod locked-state transitions, keybag and APFS volume unlock, and locks from the side button.
Observed: iOS 16.5, 17.1, 18.7.
Sources: [Notari's unlock post](https://www.ios-unifiedlogs.com/post/ios-unified-logs-unlock), [Thesis Friday #12](https://thesisfriday.com/thesis-friday-12-aul-first-glance-at-ios-26/).

**Predicates:**

- `%Screen did unlock (Was locked for%`
- `%Screen did lock (Was unlocked for%`
- `%Processed authentication request%`
- `%Transition: locked ->%`
- `%apfs is being UN-locked%`
- `%lock button source%`

## Communication and input

### logarchive call events
Telephony from the OS side, independent of the call history database: callservicesd call tracking start and end, Phone app open requests that name the originating process (a touch, Siri, or a Bluetooth head unit, which matters enormously in distracted-driving cases), Phone tab navigation, and keypad tone requests where actionIDs 1200 through 1209 map to keypad digits 0 through 9. Yes, that means a hand-dialed number can sometimes be reconstructed from sound requests. Number payloads redact to `<private>`.
Observed: iOS 16.5, 17.1, 18.7. The tone requests come from mediaserverd in the research and audiomxd on iOS 18.7, and only when keypad sounds are enabled.
Sources: Notari on [making a call](https://www.ios-unifiedlogs.com/post/ios-unified-logs-making-a-call) and [watchOS calls](https://www.ios-unifiedlogs.com/post/watchos-unified-logs-introduction-and-calls).

**Predicates:**

- `%Started tracking call%`
- `%Dialed call%`
- `%Call started outgoing%`
- `%All calls ended%`
- `%Received trusted open application request%`
- `%Resuming to tab type%`
- `%tab bar tab changed%`
- `%Incoming Request : actionID 120%`

### logarchive keyboard activity
Per-keystroke evidence of active typing, attributed to the app receiving it: keyboard touch signposts (documented under subsystem UIKitCore, logging under com.apple.TextInput on iOS 18.7) plus keyboard sound requests for character, delete, and modifier keys. Text content is not recorded; the typing activity is. Over 200,000 signpost rows on a single image, so this one is LAVA-only.
Observed: iOS 16.5, 17.1, 18.7.
Sources: [Thesis Friday #17](https://thesisfriday.com/thesis-friday-17-touch-events-on-the-ios-on-screen-keyboard/), [Notari on typing in WhatsApp](https://www.ios-unifiedlogs.com/post/ios-unified-logs-typing-and-sending-a-message-in-whatsapp).

**Predicates:**

- category `KeyboardSignposts`
- `%Incoming Request : actionID 1104%`
- `%Incoming Request : actionID 1155%`
- `%Incoming Request : actionID 1156%`

### logarchive dictation
Voice input instead of typed input: dictation start with the keyboard language code, begin and end feedback, and the assistantd record type that distinguishes keyboard dictation from a Siri request.
Observed: iOS 18.7. Zero on the other two images, which simply means nobody dictated.
Source: [Notari on dictation](https://www.ios-unifiedlogs.com/post/ios-unified-logs-the-use-of-the-dictaphone).

**Predicates:**

- `%DictationConnection startDictation%`
- `%Dictation did begin%`
- `%Dictation did end%`
- `%CSAudioRecordTypeDictation%`

### logarchive notification interactions
Notifications the user did something with: removals, group expansion, cell default actions (a tap-through into the app), long-look presentation, and replies from the notification itself. Content is not recorded; interaction is.
Observed: removal entries on all three images. Documented-only: tap-through, expansion, and reply forms.
Source: [Notari's SQL queries post](https://www.ios-unifiedlogs.com/post/ios-unified-logs-parsing-all-my-sql-queries).

**Predicates:**

- `%removing notification request%`
- `%expanding notification group%`
- `%notification cell executing default action%`
- `%will present long look%`
- `%action reply for notification%`

## Application activity

### logarchive executed apps
The original launch artifact: icon taps, application launches, and workspace transitions.

**Predicates:**

- `%Allowing tap for icon view%`
- `%Launching application%`
- `%transition source:%`

### logarchive app focus and lifecycle
The finer-grained companion: which app held focus moment to moment (an empty value means the home screen), cold starts versus resumes ("Bootstrapping ... with intent foreground-interactive" means the app was fully closed; iOS 16 spells it `application<`, iOS 17 and later spell it `app<`), scene lifecycle changes, icon taps tied to launches, and force-kills from the app switcher. A force-kill right after an event of interest is itself worth noticing.
Observed: iOS 16.5, 17.1, 18.7.
Sources: Notari's [unlock](https://www.ios-unifiedlogs.com/post/ios-unified-logs-unlock) and [SQL queries](https://www.ios-unifiedlogs.com/post/ios-unified-logs-parsing-all-my-sql-queries) posts.

**Predicates:**

- `%/device/app/inFocus%`
- `%Bootstrapping app<%`
- `%Bootstrapping application<%`
- `%killed from app switcher%`
- `%elementWithFocusBundleID changed%`
- `%Icon tapped%`
- `%Initiating launch from icon view%`
- `%Scene lifecycle state did change%`

### logarchive interface navigation
Deliberate handling between app launches: Control Center, Today view, widget visibility, home screen page scrolling.
Observed: iOS 16.5, 17.1, 18.7.
Source: [Notari's SQL queries post](https://www.ios-unifiedlogs.com/post/ios-unified-logs-parsing-all-my-sql-queries).

**Predicates:**

- `%Control Center launched%`
- `%Control Center Visible%`
- `%Setting visibility of widget%`
- `%Today view overlay%`
- `%user-initiated scroll%`

## Connectivity

### logarchive wifi status
The broadest artifact in the module, and it earned it: power state, association, reachability, SSIDs, forgotten and removed networks, scans, joins, known-network activity, per-network MAC randomisation records you can line up against router logs, keychain password retrieval, auto-join entries that carry the SSID in the clear, link loss, and per-network session duration. The 2026-08-01 additions distinguish a network picked by hand from an auto-join, which is intent evidence.
Observed: original set plus WFMacRandomisation on iOS 18.7; password retrieval, auto-join with SSID, link loss, and connection time on iOS 16.5 and 17.1. Documented-only: `manual association`.
Sources: Notari's [WiFi and airplane mode](https://www.ios-unifiedlogs.com/post/ios-unified-logs-wifi-and-airplane-mode) and [SQL queries](https://www.ios-unifiedlogs.com/post/ios-unified-logs-parsing-all-my-sql-queries) posts.

**Predicates:**

- `%WiFi state changed:%`
- `%Toggled WiFi state%`
- `%is WiFi associated?%`
- `%link status changed%`
- `%reachability changed%`
- `%ISNetworkObserver%`
- `%ForgetSSID%`
- `%en0: SSID%`
- `%Removing Lease SSID%`
- `%SysMon: WiFi state changed:%`
- `%WiFiManagerClientRemoveNetworkWithReason:%`
- `%WiFiSecurityRemovePassword%`
- `%AlwaysOnWifi:%`
- `%WiFiDeviceManagerSetNetworks:%`
- `%Scanning For Broadcast found:%`
- `%Scanning Remaining Channels%`
- `%WiFiSettlementObserver _handleScanResults%`
- `%Attempting to join%`
- `%WiFiLQAMgrSetCurrentNetwork: Joined SSID:%`
- `%Preparing background scan request for %`
- `%WiFiNetworkPrepareKnownBssList%`
- `%to list of known networks%`
- `%{AUTOJOIN, SCAN*} Scanning 2Ghz Channels found:%`
- `%{AUTOJOIN, SCAN*} Scanning 5Ghz Channels found:%`
- `%WFMacRandomisation%`
- `%manual association%`
- `%Copy password for Network%`
- `%Attempting auto join association%`
- `%Link went down%`
- `%Total connection time%`

### logarchive bluetooth status
Bluetooth power and state, device connections and disconnections, hands-free activity, call state updates, A2DP streaming, and link quality.

**Predicates:**

- `%Bluetooth state changed%`
- `%Sending new bluetooth state%`
- `%Bluetooth state changed PoweredOn%`
- `%ServiceManager disconnection result for%`
- `%Device type is%`
- `%is asking to connect device%`
- `%Received connection result for%`
- `%Received disconnection result for%`
- `%Received handsfree disconnection%`
- `%Sending ring notification for call%`
- `%Accepting incoming audio connection%`
- `%Received voice audio connected%`
- `%Stopping A2DP audio streaming%`
- `%Bluetooth A2DP device%`
- `%Bluetooth Daemon: A2DP streaming%`
- `%Starting Media connection to device%`
- `%Received voice disconnection%`
- `%Disconnecting audio from device%`
- `%Audio was already disconnected%`
- `%Toggled Bluetooth state from%`
- `%CUBluetoothDevice%`
- `%handsfree device disconnected%`
- `%handsfree device connected%`
- `%Bluetooth state updated%`
- `%Bluetooth power is now off%`
- `%Bluetooth state%`
- `%Sending call state update%`
- `%A2DP LinkQualityReport%`

### logarchive bluetooth pairing
Discovery and pairing rather than reconnection: bluetoothd `Device found: CBDevice` records that carry the accessory name, Bluetooth address, and product identifiers in the clear (the iOS 16.5 image logged a neighbor's AirPods by name, which tells you exactly how much this sees), plus pairing session lifecycle entries including rapportd Continuity pairing.
Observed: discovery and "Pairing completed" on iOS 16.5 and 17.1. Documented-only: the pairing dialog forms (pairing started, numeric comparison, SDP), because no new pairing happened in our windows.
Source: [Notari on Bluetooth pairing](https://www.ios-unifiedlogs.com/news/bluetooth-pairing).

**Predicates:**

- `%Device found: CBDevice%`
- `%pairing complete%`
- `%pairing started%`
- `%numeric comparison%`
- `%Running SDP%`

### logarchive personal hotspot
Tethering and wireless-modem state changes.

**Predicates:**

- `%Tethering is now enabled with%`
- `%Received notification that wireless modem state changed%`
- `%Previous tethering state was%`

### logarchive SIM and cellular state
SIM slot status values, cellular data network type changes, and itunestored's view of the network type, which catches WiFi-to-cellular fallback. Slot status records state at logging time, not the moment a card moved.
Observed: iOS 16.5, 17.1, 18.7.
Source: [Notari's WiFi and airplane mode post](https://www.ios-unifiedlogs.com/post/ios-unified-logs-wifi-and-airplane-mode).

**Predicates:**

- `%kCTSIMSupportSIMStatus%`
- `%dataNetwork changed to%`
- `%disabling dataNetwork%`
- `%ISNetworkObserver: Set network type%`

### logarchive airplane mode
All the enabled/disabled/active/inactive variants, plus the 2026-08-01 toggle forms where the logging process tells you how it was done: SpringBoard means Control Center, Preferences means Settings, assistant means Siri. The iOS 26 CoreTelephony state reads are deliberately not collected; they are polls, not events, and the artifact notes say so.
Sources: [Notari](https://www.ios-unifiedlogs.com/post/ios-unified-logs-wifi-and-airplane-mode), [Thesis Friday #13](https://thesisfriday.com/thesis-friday-13-aul-detecting-airplane-mode-activation-in-ios-26-beta/).

**Predicates:**

- `%Airplane Mode is now 1%`
- `%Airplane Mode is now On%`
- `%Setting airplane mode to true%`
- `%Airplane mode now active%`
- `%enabling airplanemode%`
- `%Airplane mode changed%`
- `%Airplane Mode is now 0%`
- `%Airplane Mode is now Off%`
- `%Setting airplane mode to false%`
- `%Airplane mode now inactive%`
- `%Airplane mode Disabled%`
- `%Toggle AirPlane Mode state%`
- `%Setting airplane mode enabled%`

### logarchive AirDrop
The device's rotating AirDrop ID (observed in the clear: `Current AirDrop ID is f6f8ae502871`), discoverability scanning mode (Everyone, Contacts Only, Off), SharingDaemon state dumps with device model and battery level, share sheet activation, and transfer entries. AirDrop IDs rotate, so an ID ties activity together only within a session.
Observed: ID, scanning mode, and state dumps on iOS 17.1; share sheet and `startSending` on iOS 18.7. Documented-only: incoming transfer and accept/decline forms.
Source: [Sarah Edwards, Quarantine Edition Entry 11](https://www.mac4n6.com/blog/2020/6/5/analysis-of-apple-unified-logs-quarantine-edition-entry-11-airdropping-some-knowledge).

**Predicates:**

- `%AirDrop ID%`
- `%SharingDaemon State%`
- `%Scanning mode%`
- `%startSending%`
- `%New incoming transfer%`
- `%alertLog: idx:%`
- `%Activating com.apple.sharing.sharesheet%`

## Device state and power

### logarchive power events
Boot and orderly shutdown markers: the kernel iBoot version line at startup, SpringBoard's orientation-deferral shutdown notice, and locationd shutting down. Pair these with the Sysdiagnose shutdown.log artifacts, which as of this week also carry Kaspersky's iShutdown triage heuristics: per-process shutdown delays and location indicators for the directories their Pegasus, Reign, and Predator analysis found malware delaying reboots from.
Observed: iOS 16.5 and 17.1; locationd form on 18.7.
Sources: [Notari's unlock post](https://www.ios-unifiedlogs.com/post/ios-unified-logs-unlock), [Kaspersky's shutdown.log research](https://securelist.com/shutdown-log-lightweight-ios-malware-detection-method/111734/).

**Predicates:**

- `%iBoot version%`
- `%Deferring device orientation updates for reason: shutdown%`
- `%locationd shutting down%`

### logarchive time change
Clock shifts, the system's significant time change broadcast, and the timed manual-time-setting entries that record a clock set by hand on the device. That last family is anti-forensics evidence and it is documented-only so far; none of our images had a hand-set clock, and honestly I am glad.
Sources: [Notari on clock trust](https://www.ios-unifiedlogs.com/post/ios-unified-logs-don-t-trust-the-clock-timestamp).

**Predicates:**

- `%Time change: Clock shifted by%`
- `%Significant time change%`
- `%TMSetManualTime%`
- `%setting manual time%`

### logarchive battery state
Charge level changes posted by powerd and battery info updates from PowerUIAgent. A charge curve corroborates charging claims and powered-on state.
Observed: iOS 16.5, 17.1, 18.7.
Source: [Notari's SQL queries post](https://www.ios-unifiedlogs.com/post/ios-unified-logs-parsing-all-my-sql-queries).

**Predicates:**

- `%Battery capacity change posted%`
- `%battery info changed to%`

### logarchive USB and power connections
Cable attach and detach at two layers: powerexperienced plugin state changes and the kernel cable-detect shim. Fair warning from someone who processes his own evidence: your acquisition produces these too. The observed iOS 18.7 shim message is `AppleUSBCableDetect 1`, not the documented VBUS/CON_DET form, which is why the predicate matches on the shim name.
Observed: iOS 16.5, 17.1, 18.7.
Sources: Thesis Friday [#9](https://thesisfriday.com/thesis-friday-9-aul-connecting-a-usb-cable/) and [#20](https://thesisfriday.com/thesis-friday-20-project-stark-forensic-reconstruction-of-the-carplay-handshake/).

**Predicates:**

- `%plugin state changed to%`
- `%IOAccessoryUSBConnectShim%`

## Media, audio, and camera

### logarchive media playback
The MediaRemote category: now-playing state with the originating app's bundle id, playback state changes, and route information. Sarah Edwards documented duration, elapsed time, and AirPlay target names in these entries. Activity and alibi evidence.
Observed: iOS 16.5, 17.1, 18.7.
Source: [Sarah Edwards, Quarantine Edition Entry 9](https://www.mac4n6.com/blog/2020/5/22/analysis-of-apple-unified-logs-quarantine-edition-entry-9-we-all-know-youre-binging-netflix-now-playing-on-your-apple-devices).

**Predicates:**

- category `MediaRemote`

### logarchive audio status
Playback state, volume-button presses, volume changes, and playback queue invalidation.

**Predicates:**

- `%AudioQueueIsPlaying%`
- `%VolumeIncrement%`
- `%rawVolumeIncreasePress%`
- `%rawVolumeDecreasePress%`
- `%Volume active%`
- `%PlaybackQueueInvalidation%`
- `%volumeValueDidChange%`

### logarchive audio routes
Where the sound went: receiver, speaker, or a Bluetooth device, for calls and other audio sessions. The research shows Bluetooth routes carrying the accessory MAC address, which is hands-free-versus-handset evidence during a call.
Observed: iOS 16.5, 17.1, 18.7.
Source: [Notari on calls and audio output](https://www.ios-unifiedlogs.com/news/ios-unified-logs-calls-and-audio-output).

**Predicates:**

- `%vaemConfigurePVMSettings%`
- `%vaemVADRouteChangeListener%`
- `%cmsmActivateEndpointFromRouteDescription%`
- `%currently activating endpoint%`

### logarchive camera capture
The capture chain from shutter to library: capture mode changes, moment capture begin and commit, still image capture, and assetsd adding the result to the photo library, with IMG_ filenames when not redacted. Ties a specific photo's creation to hands-on camera use, and survives the photo's later deletion for as long as the log entry lives.
Observed: the full chain on iOS 18.7, elements on 16.5 and 17.1.
Source: [Notari's SQL queries post](https://www.ios-unifiedlogs.com/post/ios-unified-logs-parsing-all-my-sql-queries).

**Predicates:**

- `%will change to: Photo%`
- `%MomentCapture%`
- `%Still image capture type%`
- `%IrisWillBeginCapture%`
- `%added photo to library%`
- `%added video to library%`
- `%Created asset IMG%`

### logarchive flashlight
Flashlight controller and AVFlashlight activity, including the spaced and unspaced AVFoundation variants because iOS could not pick one.

**Predicates:**

- `%[Flashlight Controller]%`
- `%<<<<AVFlashlight>>>>-%`
- `%<<<< AVFlashlight >>>>%`

## Motion and vehicle

### logarchive motion state transitions
Motion-state transition messages.

**Predicates:**

- `%Motion State Transition:%`

### logarchive driving state
Vehicular motion classification: wifid CMMotionActivity driving start and stop, locationd vehicular episode markers, Driving Focus engagement, and the pedestrian-after-driving alarm that marks the moment someone exits a vehicle. Two boundaries the research draws and I will repeat: these entries do not distinguish driver from passenger, and the classifier fires on other transport too. It also came with a lesson in humility: the original pattern for the locationd marker was missing a space and never matched real data. Fixed now, validated now.
Observed: iOS 16.5 and 17.1.
Source: [Notari on driving](https://www.ios-unifiedlogs.com/post/ios-unified-logs-driving).

**Predicates:**

- `%MotionState: Driving%`
- `%vehicularStartTime%`
- `%PedestrianAfterDriving%`
- `%Engaging Driving%`
- `%com.apple.donotdisturb.mode.driving%`
- `%ATXModeDrivingFeaturizer%`

### logarchive navigation
Apple Maps guidance prompts: route start, maneuvers, distance callouts, arrival.

**Predicates:**

- `%Starting route to%`
- `%Proceed to the%`
- `%Proceed to\%`
- `%Turn right%`
- `%Turn left%`
- `%roundabout%`
- `%first exit%`
- `%Stay in the%`
- `%parking lot for%`
- `%of a mile%`
- `%In about%`
- `%then arrive%`
- `%your destination%`
- `%At the light%`
- `%Arrived\%`

## Emergency

### logarchive emergency SOS engine
sosd status broadcasts and flow state, including the paired-device trigger entry documented from an Apple Watch. Read the boundary carefully: these broadcasts appeared on devices with no known SOS use, so presence alone does not show an SOS call. Payloads redact.
Observed: broadcasts and flow entries on iOS 16.5 and 17.1. Documented-only: the paired-device trigger.
Source: [Thesis Friday #19](https://thesisfriday.com/thesis-friday-19-emergency-sos-decoding-the-cross-device-help-handshake/).

**Predicates:**

- `%broadcasting SOSStatus%`
- `%flowStartedOnEitherDevice%`
- `%sosTriggeredOnPairedDevice%`

## The wide net

**logarchive artifacts** is the collection everything above filters from, and it holds predicates that do not have a dedicated report yet: screenshots, charger connection state, CarPlay connection events, device orientation, Siri speech request sessions, Apple Account authentication, contact-detail presence, walking bouts, accessory connections, brightness, ringer state, and the Emergency SOS claw gesture. They are all in LAVA under the broad collection. When one of them earns a dedicated artifact, it will move up into this list.

## What did not make the cut, and why

Transparency section, because nobody tells you what their tool is missing:

- **CarPlay session detail.** Thousands of promising "CARSession" matches turned out to be thermalmonitord's `carSessionActive` flag. The vehicle-UUID entries Thesis Friday documented did not appear in any of our images. CarPlay connection events remain covered; per-vehicle attribution waits for validation data.
- **TCC permission changes.** On iOS those entries are volatile and never reach the logarchive. TCC.db is the durable source. This one is macOS-only evidence.
- **evaluatePowerMode and the CoreTelephony airplane reads.** Present by the tens of thousands, but they are state polls, not events. Collecting them would bury signal in noise.
- **Still hunting validation data for:** AirDrop transfer accept and decline, the Bluetooth pairing dialog sequence, watch-relayed call invites, manual clock setting, and Back Tap gestures. All documented, all in the module as documented-only patterns or noted in the research, all waiting for an image where the event actually happened.

That last list is an invitation. If you have a test device and twenty minutes, generate one of those events, pull the logs, and check the patterns. If they hold, send a pull request or just tell me. If they drifted, definitely tell me. This module got its last two waves of artifacts exactly that way: published research plus somebody bothering to validate it against real extractions. The LEAPPs are free and open source, yesterday, today, tomorrow, and forever, and they grow when the community feeds them.

Good stuff lives in these logs. Go find yours.

For questions, updates, and my current contact links, visit [abrignoni.github.io](https://abrignoni.github.io/).
