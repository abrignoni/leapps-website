---
title: You down with MMKV?
date: 2026-09-04
author: Alexis Brignoni
tags: [iLEAPP, ALEAPP, MMKV, artifacts, research, tools]
excerpt: An interview with MMKV, the key-value store inside TikTok, Discord, Coinbase and more than a billion WeChat accounts. It never takes a note down, its neighbor knows when it is locked, and one zero byte means three different things.
---

# You down with MMKV?

**MMKV:** Yeah you know me!!

**Brigs:** Excuse me sir. I actually don't know you. Who are you and why you are here?

**MMKV:** Wow. Okay. I'm MMKV. Tencent built me for WeChat and gave me away to the world in 2018. I'm a key-value store. An app hands me a name and a value, I hold on to them, and I hand them back fast. Faster than the storage that came with the phone.

You've walked past me in extractions for years. Usually I'm sitting in a folder called `mmkv`.

**Brigs:** Woah. That's a lot. Before we unpack all of that, are you really that popular? I had never heard of you till today.

**MMKV:** Popular enough that you should have. WeChat runs on me, and Tencent's own quarterly report counts more than a billion accounts a month. Outside China I turn up in TikTok and Coinbase on iOS, in Temu and SHEIN on Android, and in Discord on both.

And I'll tell you a secret. You didn't have to take my word for it. In your own test phones, the ones you keep for building parsers, there are about fifteen hundred of my files. You just never opened one.

**Brigs:** Dang, calling me out. Ok, ok. Touché. A billion users is a lot of people. If I understood correctly you are Chinese. But now you belong to the world, if I heard you right. How come? What does that mean?

**MMKV:** My makers are Chinese. Tencent, the company behind WeChat, wrote me for their own app. Then in 2018 they put my entire recipe on GitHub with a license that says anyone can use it, for free, in anything. That's what open source means. Any developer anywhere can drop me into their app, and thousands did.

It also means something nice for you. The code that writes my files is public. You don't have to guess how I lay out my bytes. You can read it.

**Brigs:** Can I? You said you're a key-value store. Do you sell keys in a store at a great value? How can I read that?

**MMKV:** Very funny. No. Think of a wall of sticky notes. Each note has a label on top and something written under it. The label is the key. What's under it is the value.

`dark_mode` and under it, on. `last_login` and under it, a time. `draft_message` and under it, whatever the user was typing. That's it. An app keeps its little facts on my wall instead of in a database, because a database is a lot of ceremony for a sticky note.

Reading me is reading the wall. Label, note, label, note, top to bottom.

![MMKV drawn as a pad of sticky notes, pointing at a wall of seven notes in file order. The key display_name appears twice, the older one faded. The key draft appears twice, the second with nothing written under it.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-09-04-you-down-with-mmkv/you-down-with-mmkv-wall.webp)

*Figure 1: MMKV's wall, in the order the notes went up. The faded notes are older writes. A label with nothing under it is a removal.*

**Brigs:** Oh ok. Cool. That reminds me of my friend JSON, not to be confused with Jason Voorhees, who is not my friend. I like your label and the text under it analogy. Let's say I want to get rid of a note and what's written on it. How do you do it?

**MMKV:** JSON is fine. A bit chatty. He can't tell you it's raining without curly braces, quotation marks around every word, and a comma after each one, and he falls apart if one comma is out of place. The other Jason is worse, granted, but JSON has ruined more Mondays.

Here's the thing about getting rid of a note. I don't take it down. I never take anything down. I stick a new note at the end of the wall with the same label and nothing written under it. That blank note is my way of saying "this one is gone."

The app reads the wall top to bottom, gets to the blank note, and forgets the label ever existed.

The original note is still on the wall.

**Brigs:** Well, you had my curiosity, now you have my attention. Are you saying that all those values can be recovered?

**MMKV:** Recovered is a strong word. Recovered sounds like you had to dig. You don't. They're just there, in the file, in plain sight, in order. Every old version of a note, every blank "this one is gone" note, sitting right where I stuck them.

The app never shows them to anyone because the app only cares about the last note under each label. You're not the app.

One catch. My wall isn't infinite. Ask me what happens when I run out of room.

**Brigs:** Fair enough sir, what happens when you stretch and your feet stick out because you ran out of bed sheet?

**MMKV:** Then I clean house. I take every label, keep only the newest note under it, throw away the old versions and the blank ones, and put the survivors back on a fresh wall. If the fresh wall is still too small, I get one twice the size. Then I go back to sticking notes at the end.

So the history lives between cleanings. Catch me before one and it's all there. Catch me right after and you get only what the app sees.

I do keep count of how many times I've cleaned house, though. Not on the wall. In a little file that lives next to me.

![The same wall before and after a cleaning. Before: seven notes including two older writes and a removal. After: four notes, only the live ones, renumbered from zero.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-09-04-you-down-with-mmkv/you-down-with-mmkv-cleaning.webp)

*Figure 2: a cleaning keeps the newest note under each label and throws the rest away. Catch the file before one and the history is there.*

**Brigs:** So you have a neighbor!!! Me too. Mine puts way too loud music at inopportune times, but I like what they are playing, so it's ok. Tell me about your neighbor. What's its name? Does it do more than keeping count on how many times you clean your house?

**MMKV:** Same name as me with `.crc` tacked on the end. Not a creative family.

It does four things. It keeps a fingerprint of my wall, a checksum, so the app can tell if I got damaged. It keeps a version number, so the app knows how old my layout is. It keeps that house-cleaning count. And it keeps sixteen bytes that are all zeros.

Unless someone locked me. Then those sixteen bytes aren't zeros anymore, and that's how you know.

**Brigs:** Lock you? You have all those keys and they can still lock you? Tell me about that. Who would lock you in your house and why?

**MMKV:** The app locks me. Not against itself, against you. A developer who worries about my file walking off a phone can tell me to scramble everything on the wall with a secret only the app holds. Same wall, same notes, but every label and every value is gibberish until it's unscrambled.

Those sixteen bytes in my neighbor's file aren't the secret. They're the random starting point for the scramble, and they change every time I clean house. Zeros means nobody locked me. Anything else means somebody did.

In your test phones, SHEIN, WeChat and TikTok lock some of their walls. Most don't bother: of the fifteen hundred files of mine you have, about a hundred are locked.

And here's the trap. A locked wall doesn't look locked. It looks like a wall full of labels. Bad ones.

![The same three notes shown twice: readable on the left, and scrambled into hexadecimal on the right after AES encryption. Below, the .crc neighbor holds sixteen non-zero bytes.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-09-04-you-down-with-mmkv/you-down-with-mmkv-locked.webp)

*Figure 3: a locked wall keeps its shape and loses its meaning. The sixteen bytes in the .crc file are the tell, and they are the starting point for the scramble, not the secret.*

**Brigs:** Oh, I guess snitches really do get... So in order to avoid it they can take all the information, recent or old, and just make it impossible to read. They put the data in a crypt, one might say, or like they say in Spanish, "en cripta." How can the information be unscrambled or taken out of the crypt? Decrypted?

**MMKV:** With the secret, and only the secret. The scramble itself is standard, it's AES, the same thing your bank uses. Nothing clever to break. Hand the secret and the sixteen bytes from my neighbor to anything that speaks AES, and the wall reads clean again.

The secret is not in my file. It's not in my neighbor's file. The app has it, and the app has to keep it somewhere it can reach without asking the user. Sometimes that's the phone's keychain. Sometimes, and developers hate when I say this, it's sitting in the app's own settings file two folders over.

**Brigs:** Well, life is all about the details and software is all about proper implementation, I guess. Talking about implementations, let me go back to your keys and values. What can the keys and values be? Numbers? Letters? Emojis? What can be stored there?

**MMKV:** Labels are always text. Any text. Letters, numbers, emoji, whatever the developer typed when they named the note.

What's under the label is anything. A number. A yes or no. A sentence. A whole document. A picture, if the app is feeling lazy. I don't care what it is. To me it's just a run of bytes with a length in front of it.

And that's the part that surprises people. I don't write down what kind of thing it was. The app knows it stored a number, so the app reads a number. I never wrote "number" anywhere. The wall has the label and the bytes, nothing else.

**Brigs:** I am actually surprised. Let's say the application puts in a long series of bytes that could be interpreted as a fractional number or as a fixed integer. How would I, looking at the value, know how to interpret it?

**MMKV:** From the value alone, you can't. Not with certainty. Eight bytes under a label could be a decimal number, a whole number, a date, or the first eight letters of something. I stored the bytes. The meaning went home with the app.

Some shapes give themselves away. A note that's "a length, then exactly that many bytes" was almost certainly text. A short note that's built the way I build whole numbers was almost certainly a whole number or a yes/no. Those two you can call with a straight face.

The rest, you go ask the app. Read its code if it's open. Or take a phone you control, do something in the app, and watch which note changes and what it turns into. The label helps too. Nobody names a note `last_login_ms` and puts a photo under it.

**Brigs:** I want to really underline something you just said. To understand some values it might require putting known data in a device that has an app that has you, in order to see how you store it, to then understand how to interpret it. I wish more people would take the time to do so instead of assuming, because we all know what happens when you assume...

**MMKV:** You make an app out of you and me. I'll give you the best example I have.

One single byte, zero. Under one label it means the number zero. Under another it means "false." Under a third it means an empty piece of text, the user cleared the box. Same byte. Three meanings. Nothing on my wall tells you which.

Assume, and you'll write "the user turned this off" when the user actually typed nothing. Put known data on a phone, watch what I write, and you'll know. That's the whole difference between reading me and guessing at me.

![One sticky note holding a single byte, 00, with three thought bubbles reading: the number 0, false, and empty text.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-09-04-you-down-with-mmkv/you-down-with-mmkv-zero-byte.webp)

*Figure 4: one byte, three meanings, and nothing in the file to separate them.*

**Brigs:** Your example is on freaking point and totally on target. I couldn't agree more. Ok, so you are really popular, like billion-user popular. Are there many parsers out there that read your data independent of the apps that use you as a way to store it?

**MMKV:** Fewer than you'd think for a billion users. I found four small ones on GitHub, hobby projects, a few dozen stars between them. One in Python, one in Rust, one in TypeScript, one in Go. Most of the world just lets the app read me and never looks at the file.

And they don't all agree with each other about my first few bytes. That's a sore spot. Ask me about it.

**Brigs:** I am going to ask then. I do some Python coding. Tell me about the Python one. Where can it be found? Can you describe it?

**MMKV:** On GitHub, under a user named spak9. The project is mmkv_visualizer. Python, but it doesn't run from a terminal. It's a web page: you drop my file on it, and the Python runs right inside your browser, lays my wall out as a table, and nothing leaves your machine.

It's the most popular of the four, about forty stars, and it will unscramble a locked wall if you hand it the secret. It reads my neighbor's file for the sixteen bytes and everything.

It also skips right past my first few bytes with a comment that says, more or less, "no idea what this is."

**Brigs:** What about the other three? Do they also not know what some stuff means?

**MMKV:** Same spot, same shrug. The Rust one decrypts too, and it reads that number and says "no idea what this is, probably not used anyway." The TypeScript one says "I don't know this value, probably a bunch of F's" and steps over it.

They're lucky. That number is the size of all the notes that follow, it changes width, and reading it and tossing it is exactly the right thing to do, even if they didn't know why.

The Go one is the careful one. It reads my neighbor's file, checks my checksum, checks my size, can even unscramble a locked wall. And then it assumes that number is always four bytes long and skips four. On some of my files it's one, two or three. On those walls it starts reading in the middle of the first label.

Careful and wrong. That's the one that worries me.

**Brigs:** You mention that data needs to be tested (verified) and now it seems you are telling me that processes need to be tested (validated) too.

Let me ask you about another alternative. Have you heard about the LEAPPs project? If you did, does it have some way of getting your sticky notes out?

**MMKV:** Heard of them. They've been reading my walls since the Discord and Coinbase artifacts on iOS, and JusTalk and Xiaohongshu on Android. All four go through one small shared reader that lives inside iLEAPP and ALEAPP.

It reads the wall top to bottom, gives you every note including the old versions and the blank ones, and can also give you just what the app sees. It checks my neighbor for the lock and refuses to read a locked wall instead of handing you gibberish.

It also had the same blind spot the Go one has. Until this week.

**Brigs:** I heard that the person that came out with the mmkv_parser.py must be really smart for making the parser AND fixing the blind spot.

**MMKV:** Smart. Sure. I heard the LLMs go brrrrr.

Both the reader and the fix came out of a machine that types very fast. That's not the impressive part. The impressive part is what happened after the typing: twelve little tests, each building one of my files by hand, byte by byte, at every width my number comes in. Eleven of them fail on the old reader and pass on the new one. Then the new one got pointed at every one of my files in your test phones to see what changed.

The typing is cheap now. The checking is the job.

**Brigs:** You are too kind, but also a lot of correct. Verification and validation is where it's at and where it will always be.

Is there anything I have missed regarding you and who you are that I should know?

**MMKV:** Three things.

One, as of this week that reader isn't tucked inside the LEAPPs anymore. It has its own home, [abrignoni/mmkv-parser](https://github.com/abrignoni/mmkv-parser) on GitHub. iLEAPP and ALEAPP copy it in byte for byte, and a check fails their builds if anyone edits the copy instead of the original. Fix me once, in one place.

Two, it comes with a command line. Point it at one of my files and you get every note in order, or just what the app sees, or a polite refusal if I'm locked. Ask me and I'll show you.

Three, don't judge me by my file size. I'm padded out with zeros to a round number, so a sixteen kilobyte file might hold five notes. The real length is written in my first four bytes. Everything past that is empty wall.

**Brigs:** Let me tell you, I never judge anyone by their size. There is beauty in all sizes and all the shapes of files. No doubt about it.

Tell me about this command line, because one of the other parsers was like a webpage and that seems hard to use at scale. How does the mmkv-parser work on the command line?

**MMKV:** One command. Point it at my file and it prints my wall, one note per line:

```text
$ python -m mmkv_parser dump demo.mmkv
0	'user_id'	48213
1	'display_name'	'alpha'
2	'last_login_ms'	1785482702086
3	'display_name'	'alpha two'
4	'draft'	'typed but never sent'
5	'draft'	<removed>
6	'notifications'	1
```

Three columns. Where the note sits on the wall, counting from zero. The label. What's under it. Look at `display_name`: two versions, both there. Look at `draft`: written, then the blank note that erased it.

Add `--live` and you get only what the app sees, the last note under each label, with the erased ones gone. Point it at a locked wall and it stops with one line saying so, instead of printing gibberish.

The reader is a single Python file with no dependencies. Install it with pip from GitHub, or just copy that file next to your script and import it. Scale is a `for` loop.

**Brigs:** I --live for this. (Did you see what I did there?) Your example is crystal clear. Simple command and out comes the data. Give me your honest opinion, should this script have a GUI and a way to unscramble the notes if the key is provided?

**MMKV:** Honest opinion. Skip the GUI. The thing that makes this reader useful is that it's one file with no dependencies, so iLEAPP, ALEAPP, or your own script can swallow it whole. A window on top is a second thing to maintain and a second thing to break, and spak9's web page already covers the point-and-click crowd. Let the LEAPPs be the GUI.

Unscrambling, yes. Add it. But make me say it back to you: the examiner hands over the secret. The tool never goes hunting for it, never guesses, and never quietly falls back to reading gibberish when the secret is wrong. Secret in, clean wall out, or a clear refusal. And write down where apps tend to keep that secret, because that's the real work, not the AES.

One more, since you asked for honest. The newest version of me stopped promising to keep my length in those first four bytes. It moved that job to my neighbor. Every file in your test phones still agrees, but the day one doesn't, the reader should trust the neighbor first.

**Brigs:** This conversation has been so illuminating. I will tell the developer 🤖 to add those features in the really near future.

Look, I can't thank you enough for talking to me today. I can confidently say I know you, and for that I am down with MMKV. Isn't that awesome?

**MMKV:** Awesome is a strong word. Accurate is better. An hour ago I was an opaque blob next to a smaller opaque blob. Now you can read my wall, spot my blank notes, tell my locked walls from my open ones, and you know not to trust a single zero byte without asking the app.

So yes. Now you know me.

Go open an extraction. There's a folder called `mmkv` in it somewhere, and it has been waiting.

**Brigs:** Will do. See you soon!

**MMKV:** You will. Every phone, every app, right next to my neighbor. Bring the parser.

---

**PD:** Since this conversation the reader learned to do the two things MMKV asked
for. Version 1.1.0 opens a locked store when you hand it the key, as text or as
hex, from the command line or from code. It still never goes looking for a key, it
ignores one for a store that is not locked, and a key that does not work is refused
instead of printing gibberish. It also takes the length of the data region from the
`.crc` file where that is the record, which is the value MMKV itself reads.

```text
$ python -m mmkv_parser dump --key 'the key the app uses' locked.mmkv
```

iLEAPP and ALEAPP both carry the new version.
