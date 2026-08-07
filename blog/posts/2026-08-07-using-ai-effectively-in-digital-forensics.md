---
title: Using AI Effectively in Digital Forensics
date: 2026-08-07
author: Alexis Brignoni
tags: [AI, LLM, DFIR, opinion]
excerpt: A decent version of most digital forensics software can now be made at home, in a few hours, by a user that does not code. What does that mean for vendors and for us as users, and what actually makes someone an expert in the AI context? Five qualities.
---

# Using AI Effectively in Digital Forensics

In a [previous blog post](https://www.leapps.org/blog-post?post=2026-07-11-the-rules-keep-changing) I waxed a little about how the rules in our field are changing. This is because the industry that produces our source data, software development, is bearing the brunt of those changes right now.

Digital forensics software development is starting to feel the impact. Are you a mapping software developer? A company that sells artifact parsing? Do you sell a timelining tool, a fast triage solution, a log management suite? A decent version of any of these can now be made at home, in a few hours, by a user that does not code. Give that same user a few more tokens and a weekend, and what used to be your competitive advantage is gone.

## What might this mean for these companies, and for us as users?

**Coding has been democratized.** Heck, I expect AI tools to be coding straight in assembly in no time. Selling software as the product might not be the main revenue stream for software companies much longer. The model that kept a company like Red Hat in business might become the model for everybody. There is no moat anymore, so the move to other capabilities, like professional services or infrastructure management, needs to happen yesterday.

**Users will use AI to build or reverse engineer what these companies used to do for them.** This carries a lot of risk, of course, but it will happen anyway. How are companies responding? There are already offerings in the market for AI tools that will parse those data structures for you. The pitch is to use their expensive AI to find artifacts so you don't have to point your own AI at the problem. I'll be transparent: I don't see it. There is no cost advantage in being an AI wrapper company, and the target market for these solutions is the non-expert. Folks that will go and generate all sorts of parsed artifacts with AI and have no way of knowing if any of it is true.

Referencing my [previous blog post](https://www.leapps.org/blog-post?post=2026-07-11-the-rules-keep-changing) again, LLMs will have a role in our field as long as they are used properly. What seems like a risky proposition is continuing to hand AI tooling, be it a chat bot or an LLM powered artifact parser, to individuals that are not qualified in any sense to verify the output or validate the deterministic processes (like code) that come out of an LLM.

The question then becomes: what makes a user an expert in this context?

## The digital forensics AI expert

The digital forensics AI expert has certain qualities and characteristics.

**1. Knows how to code.** Sorry, but you need to read and write code effectively to manage the output of these tools. I use LLMs extensively to generate deterministic code, and I not only check the code, I read every transcript of the LLM "thinking" process. The number of times I had to redirect it away from a catastrophe is more than I can count. Now imagine letting the LLM loose with no supervision at all. That vision will not hold up in the market long term, and it will hold up even less in court.

**2. Uses LLMs to make deterministic code instead of relying on the stochastic conclusions of the LLM itself.** I have no issue using a stochastic process to get me to a deterministic output I can verify and validate. That is the whole trick. Repeatable code mitigates the hallucination risk, saves money (no need to spend tokens answering the same question twice), and gives you output you can actually defend. Why spend your life verifying every conclusion an LLM hands you when you can have it build deterministic code that you validate once and use for present and future casework? Which leads directly to the next one.

**3. Knows how to verify and validate.** This means constantly building properly documented test data into an ever growing corpus of sample images. Those samples are what let you validate the deterministic code and catch regressions as you develop answers to new questions. A conclusion supported by 50 data samples across different OS and hardware versions is way more solid than whatever the AI said about one database from the investigation source. And understand this: there is no outsourcing here. No third party, no matter how much you pay them, will carry the responsibility and the consequences of your LLM use for you.

**4. Understands continuous integration and versioning.** Turns experience into rules and automated checks that run on every change. Knows how to roll back when something goes sideways. Leverages the memory features of these tools to codify best practices, so a lesson learned once stays learned.

**5. Knows how to manage multiple agents at once and follows every chain of thought closely.** This expert has to be the CEO and the line supervisor of these systems at the same time. Hold the big picture in your head while making sure every small piece is being implemented correctly, right?

Ours is a scientific field, and it requires testable and repeatable processes. Entropy is the default; order takes work. Only an expert can pluck out meaning that is testable and repeatable, and our field demands no less, no matter what anybody is trying to sell us.
