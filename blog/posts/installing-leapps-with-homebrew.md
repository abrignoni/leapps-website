---
title: Installing LEAPPs and LAVA on macOS with Homebrew
date: 2026-06-28
author: James Habben
tags: [LEAPPs, LAVA, macOS, Homebrew, installation]
excerpt: Mac users can install iLEAPP, ALEAPP, RLEAPP, VLEAPP and LAVA with a few Homebrew commands from the LEAPPs tap.
---

# Installing LEAPPs and LAVA on macOS with Homebrew

*Updated October 1, 2026: iLEAPP, ALEAPP and RLEAPP are now one program each, so their casks install the app and the command line together, and Homebrew 6 asks you to trust the tap before adding it. The commands below reflect both changes.*

If you use a Mac for forensic work, you probably already have a small pile of tools installed through Homebrew. It is one of those quiet utilities that makes a workstation feel civilized: install the thing, update the thing, move on with your day.

The LEAPPs tools now fit into that workflow too.

There is an official Homebrew tap for the project at [leapps-org/homebrew-leapps](https://github.com/leapps-org/homebrew-leapps). Once the tap is added, macOS users can install the LEAPPs command line tools, the GUI apps, and LAVA with normal `brew` commands.

One quick reality check before the commands: a lot of forensic workstations are intentionally kept offline. Homebrew is happiest on a machine that can reach the internet. If your lab machine is air-gapped, this may not be all that helpful, but maybe you have a research system or a connected staging machine that can benefit from this.

## Add the tap

Homebrew 6 will not load a tap that is not one of its own until you trust it, so trust the LEAPPs tap first and then add it:

```bash
brew trust leapps-org/leapps
brew tap leapps-org/leapps
```

If your Homebrew is older and has no `brew trust` command, skip that first line.

You only need to do this once. Homebrew will remember the tap until you remove it.

## Install iLEAPP, ALEAPP and RLEAPP

Each of these is now a single program. The cask installs the app and links its command line as `ileapp`, `aleapp` or `rleapp`. Started without arguments it opens the window. Given arguments it runs as the command line.

```bash
brew install --cask ileapp-gui
brew install --cask aleapp-gui
brew install --cask rleapp-gui
```

The older `ileapp`, `aleapp` and `rleapp` formulae are deprecated and stay at the last release that had a separate command line download. If you have one installed and want the command line that comes inside the app instead:

```bash
brew uninstall ileapp
brew reinstall --cask ileapp-gui
```

## Install VLEAPP

VLEAPP still ships its command line and its GUI app separately:

```bash
brew install vleapp
brew install --cask vleapp-gui
```

## Install LAVA

For reviewing LEAPPs output in LAVA:

```bash
brew install --cask lava
```

That is the part I am happiest about. LAVA has become a really comfortable way to review LEAPPs output, especially when you are filtering tables, previewing media, or bouncing around a report during research. Being able to install it with a single Homebrew command feels right.

## Keeping everything updated

Homebrew handles updates in the usual way:

```bash
brew update
brew outdated
brew upgrade
```

If you only want to update specific LEAPPs tools, name them:

```bash
brew upgrade ileapp-gui aleapp-gui
```

For casks, Homebrew will also handle upgrades through the normal upgrade flow.

One more quick note: the Homebrew packages track *packaged releases*. They are not meant to follow every development commit between releases. If you need the newest parser work from a development branch, cloning the repo directly is still the way to do that.

## Removing tools

If you need to uninstall the VLEAPP command line tool:

```bash
brew uninstall vleapp
```

For the apps:

```bash
brew uninstall --cask ileapp-gui aleapp-gui vleapp-gui rleapp-gui lava
```

And if you ever want to remove the tap itself:

```bash
brew untap leapps-org/leapps
```

Untapping does not remove tools you already installed. It only removes the tap from Homebrew.

## A small quality-of-life win

This is not the flashiest project update, but it is one of those things that makes the tools easier to live with. New machine? Fresh lab Mac? Quick test system? Add the tap, install what you need, and get back to the actual forensic work.

That is a good kind of boring.
