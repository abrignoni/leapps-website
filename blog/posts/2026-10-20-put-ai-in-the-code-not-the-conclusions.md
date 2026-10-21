---
title: "DFIR Thoughts: Put AI in the code, not the conclusions"
date: 2026-10-20
author: Alexis Brignoni
tags: [AI, LLM, DFIR, opinion, validation]
excerpt: Handing examiners a chatbot that draws conclusions from parsed data is the wrong way to bring AI into digital forensics. Here is why, and what I do instead with a known-data corpus, tested code and CI checks.
---

# DFIR Thoughts: Put AI in the code, not the conclusions

![Scattered chat bubbles on the left throw off red dots that funnel into a pair of green code braces. On the right, one straight line of green dots runs from the braces into the center of a bullseye.](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-10-20-put-ai-in-the-code-not-the-conclusions/put-ai-in-the-code-hero.webp)

Is a chatbot the way to bring AI into our digital forensics workflows? Like all things in digital forensics, it depends. There is a good way to use AI in our work. It is not the way many of the AI tools being sold to us are doing it.

## The current state of affairs

All of my code is AI generated now. That might sound like I'm betraying everything I've said about AI before. I'm not. Please hear me out.

Much of the programming world now writes code with AI, and those who don't will fall behind soon.

A few months ago I was asking the same questions you might be asking now. Aren't we opening ourselves up to AI slop code? What about the hallucinations that are impossible to avoid? Who will verify the output?

We have answers to those questions now, and I'll get to them shortly. The fact is that with the proper safeguards, AI is a great coder, and one we can't avoid. I'd bet most of the forensic tools you use right now already have AI generated code in them.

With AI we have built capabilities into the LEAPPs in a few months that would have taken years of human work. We are not the only ones. We used to have too few tools for the work. Soon we will have too many to choose from, including the ones people put together on their own over a weekend.

That brings its own problems. People who are neither programmers nor forensic experts will put out software of questionable quality, for public or internal use, with no way to support its output in court. That is a topic for another day.

AI tools are really good at coding for two reasons. They learned from an extremely large body of code, and coding has clear finish lines. Either the code produces the expected result or it doesn't, and you can measure that.

The rub is that in digital forensics the finish lines are not that clear, and we are being sold AI implementations that assume they are.

## Where chatbots are weakest

Every time a chatbot writes a narrative, it creates an opportunity for hallucinations, overclaims, underclaims and plain errors. Why? At its core, AI is autocomplete on steroids. The less structured the task, the more random the autocomplete gets. And there is nothing less structured than drawing a conclusion from scattered facts about human actions as recorded on digital media. In my own artifact work on the LEAPPs, using frontier models, I have run into a lot of solid sounding statements that were at best too general and at worst flat wrong.

This is why having an AI go over parsed data, give you conclusions, and leaving the verification for later will be a train wreck in practice. Here's why.

### 1. The AI will be missing data

An AI chatbot from a well-known vendor in our space was being tested. After processing, the total image count it reported was lower than expected. When asked why there were so few images, it said it had excluded images it judged irrelevant, like thumbnails and thumbnail caches.

Thumbnails and thumbnail caches can be all that's left of a picture after the original was deleted. Worse, the tool decided what was relevant on its own and only said so when asked.

### 2. The AI will give you an answer that is just false

Another well-known tool was asked when a particular connection last happened. It gave the wrong answer. The user told it the correct answer and showed it where that answer was in the data. The AI agreed it had been wrong. When asked the original question again, it gave the same wrong answer.

### 3. Vendors are not providing a way to verify and validate at scale

AI can give you a million conclusions, and the vendor puts all the responsibility on the user to make sure they are right. I call this the "Google AI is sometimes stupid" card. Every Google AI response ends with a note that "AI can make mistakes, so double-check responses."

A million results? Two million? Ten billion? It's on you to make sure none of them are wrong. That's fine when little or nothing is at stake. In our field the stakes are always high. Vendors have a responsibility to make sure, to the best of their ability, that the output of their very expensive tools is not wrong. At a minimum, they should give us an automated way to verify that output at scale.

### 4. Users will run with AI output unless a verification process stops them

If there is no verification process, users will take whatever the AI tells them as gospel and run with it. Nothing is more tempting than output that confirms what you already want, or "know", to be true. As forensic examiners we should be trained to spot and resist that mindset, and still we see little of that in practice.

### 5. AI generated output will reach court, and the fallout could be far reaching

The question is not if AI will be used in court. It is not when, either, because it almost certainly already has been. The question is when its use will be noticed and challenged in our field. For all I know, that is happening right now as I type.

That means the person testifying has to be able to defend how AI was used. Saying in court that you copy-pasted what the chatbot told you into your report will not cut it.

## So how do we use AI properly when the courts are involved?

Giving everyone a chatbot is a recipe for legal disaster in digital forensics. On the flip side, not using AI at all is a recipe for disaster too, because we'd be leaving the most powerful tool we have on the table.

Here are some personal opinions. They reflect the beliefs and policies of no one but myself.

### 1. Stop marketing the chatbot to everyone

In many industries, general use of AI is fine and even encouraged. In ours it should not be. Experts have to be part of the process from the start, not just at the end, where verifying at scale becomes impossible.

I get that corporations are in the shareholder value business. We are in the stakeholder value business: the victims, the accused, the courts and the public. Treating one like the other is behind many of the problems I listed above.

### 2. Have experts study the needs of the organization and build AI tools for those needs, with safeguards

This means you don't just throw a chatbot at users. You give them a workflow that is AI enabled but constrained. Users get trained on the system like they would on any other tool.

I recognize most organizations won't have the resources to do this. Hence...

### 3. Make the experts the users of the tool

If verification and validation matter, then the people trained to do them need to be at the AI wheel. We don't hand car keys to someone without a driver's license. We shouldn't do it with AI either.

### 4. Get more experts, not fewer

The funny thing about AI is that more productivity creates a need for more knowledgeable users, not fewer. Instead of watching a whole agency use AI ineffectively, we can make a conscious choice to put it in capable hands and get the best out of it.

## What if you are the point person for AI? How do you get the best results at scale?

Again, more opinions:

### 1. Build a data corpus and keep updating it

A data corpus is a large, ever-growing collection of extractions and sample data where the contents are known. Document it as thoroughly as you can so it works as a reference you can return to again and again.

Every output needs to be run against the corpus. We validate a finding from an unknown source by seeing how the same finding shows up in a known one.

### 2. Use VMs and real devices to generate test data

Never accept a conclusion the AI drew from a sample of one. Generate test data on VMs and real devices, and add it to the corpus. The AI itself can drive the VM and collate the results. I'll confess it is really convenient and fun to watch.

### 3. Turn conclusions into static code, and test that code

Have the AI write the conclusion down as code. Then you can test that code with unit tests, regression tests, mutation tests and independent adversarial agents, and run it over the whole corpus.

Deterministic code is something you can actually review, step by step if needed, to get the assurance our high stakes work demands. Determinism doesn't make the code right. Code can be wrong the same way every time. What it gives you is an error that repeats, so you can find it, test for it and fix it once, instead of a different random answer every time you ask.

It also saves money in the long run. Instead of burning tokens asking the same questions over and over, you plug code that already has the answers into your process.

### 4. Use continuous integration (CI) rules to flag problems in the code and in any AI generated descriptions

As I said before, AI is at its weakest with narrative text. AI likes strong words. It will say a record shows "the user viewed" a message, or that a table holds "all" the user's searches, when the data only shows that a row exists. So in iLEAPP, ALEAPP, RLEAPP, VLEAPP and DLEAPP, CI runs a check on every pull request (PR) that touches Python code. It reads the name, description and notes of every artifact and fails the build when it finds that kind of wording.

Here's an example. Say an AI drafts a note that a message was "viewed by user." CI flags it, the build goes red, and we don't merge the PR until someone either rewrites it to say what the data actually shows or adds it to an allowlist with a written reason.

I built this after learning that reviews alone miss things. In one case, a claim got fixed in the code comments but stayed in the description of the same artifact, and it had to be fixed a second time. A person can miss that, and so can an AI. The check doesn't get tired and doesn't skip a field. When it can't read an artifact, because that artifact's information is built by code at runtime, it lists it as NOT CHECKED on every run, so nobody assumes it was covered.

As an expert, you need to develop the skills to do this kind of checking automatically and at scale. Trusting that you'll catch problems at the end by reading through everything won't be enough.

### 5. Document how AI was used

Keep a record of what the AI did: the model, what it was asked, what code it produced, and how that code was tested. If you can't explain how a finding was produced, you can't defend it.

### 6. Work the deterministic output and verify key findings with traditional investigative techniques

If you need more, lean on your corpus and start the process again.

## Closing

AI is not going anywhere. It is up to us to find ways to use it effectively, in a way that protects due process and the rights of the accused and gives us the repeatability the scientific method requires.

This is just a sliver of what we can do to get there. I'd love to hear how others are doing it.
