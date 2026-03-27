<h1 align="center">DorkVault</h1>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=24&pause=1000&color=2563EB&center=true&vCenter=true&width=1000&lines=Desktop+Recon+Query+Launcher;1000%2B+Structured+Techniques;Fast+Search+%7C+Filter+%7C+Preview+%7C+Launch;Windows+and+Linux+Binary+Releases" alt="Typing SVG" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/Platform-Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" />
  <img src="https://img.shields.io/badge/UI-PySide6-41CD52?style=for-the-badge&logo=qt&logoColor=white" />
  <img src="https://img.shields.io/badge/Type-Binary_Release-111827?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Status-Stable-2563EB?style=for-the-badge" />
</p>

<p align="center">
  <a href="../../releases/latest">
    <img src="https://img.shields.io/badge/Download-Latest_Release-2563EB?style=for-the-badge" />
  </a>
  <a href="../../releases">
    <img src="https://img.shields.io/badge/View-All_Releases-0F172A?style=for-the-badge" />
  </a>
</p>

---

## Overview

**DorkVault** is a desktop application for organizing, previewing, filtering, and launching search-based reconnaissance techniques from a clean local interface.

It is designed for fast target-based workflow management with a structured technique catalog, rendered query previews, category filtering, favorites, recents, and theme support.

This repository is a **binary release repository**. It distributes packaged application builds only.

---

## Core Features

* 1000+ structured techniques
* Fast search and category filtering
* Rendered query preview
* Detail panel for selected techniques
* Light and dark themes
* Favorites and recent items
* Custom local technique support
* Windows packaged executable
* Linux runnable build

---

## Downloads

Download the latest packaged binaries from the **Releases** section.

### Release Assets

* **Windows:** `DorkVault-Windows-v1.0.0.exe` or `.zip`
* **Linux:** `DorkVault-Linux-v1.0.0` or `.tar.gz`

### Quick Access

* [Latest Release](../../releases/latest)
* [All Releases](../../releases)

---

## Workflow

1. Launch **DorkVault**
2. Enter a target such as `example.com`
3. Search or filter the technique catalog
4. Select a technique from the list
5. Review the generated query preview
6. Copy the query or open it in your browser

---

## What DorkVault Can Do

* Organize search-based recon techniques
* Render target-aware query templates
* Filter techniques by category and keyword
* Preview technique details before use
* Launch supported search queries locally
* Store local favorites, recents, and custom entries

---

## What DorkVault Cannot Do

* It does **not** perform active scanning
* It does **not** exploit targets
* It does **not** bypass authentication
* It does **not** verify whether results are valid, current, or in scope
* It does **not** guarantee search engine results
* It does **not** determine whether you are authorized to assess a target

---

## Platform Notes

### Windows

* Download the Windows release asset from the **Releases** section
* Run the packaged executable normally
* Depending on system policy, Windows SmartScreen may prompt before launch

### Linux

* Download the Linux release asset from the **Releases** section
* Make the binary executable before running:

```bash
chmod +x DorkVault-Linux-v1.0.0
./DorkVault-Linux-v1.0.0
```

* If you distribute it as a compressed archive, extract it first

---

## Quick Tips

* For most techniques, enter a **domain** like `example.com`, not a full URL like `https://example.com/`
* Use the search bar to narrow large catalogs quickly
* Use category filtering to focus results faster
* The right-side detail panel contains the full description, template, and rendered query
* External engines may change over time, so results can vary
* Some techniques work better with company names, subdomains, or keywords instead of full URLs

---

## Supported Platforms

* Windows
* Linux

---

## Safety Notice

Use DorkVault only for authorized security research, defensive analysis, lab work, or permitted target assessments.

---

## Repository Contents

This repository contains only:

* `README.md`
* `LICENSE`

Release binaries are distributed through **GitHub Releases**.

Source code is **not** included in this repository.

---

## Screenshots

You can add screenshots later if you want.

Example path:

`assets/screenshot-main.png`

If you add a screenshot later, use:

`![DorkVault Main UI](assets/screenshot-main.png)`

---

## Release Policy

This repository is maintained as a **release-only distribution point** for packaged DorkVault binaries.

New builds will be published in the **Releases** section with versioned assets for supported platforms.

---

## License

This software is distributed under a proprietary **All Rights Reserved** license unless otherwise stated.

See the [LICENSE](LICENSE) file for details.
