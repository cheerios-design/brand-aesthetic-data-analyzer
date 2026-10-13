# Overview

As a software engineer, I wanted to strengthen my skills in data cleaning, numerical analysis, and visualization while working on a problem with real design and accessibility implications. The Brand Aesthetic Data Analyzer loads raw design data for digital brands, cleans it, calculates accessibility metrics, and visualizes the results.

The data set is a hand-built sample of 26 well-known digital brands, stored in brands_data.csv. Each row lists a brand's primary color, background color, and typography class (Sans-Serif, Serif, or Monospace). The hex codes were entered from my own recollection of each brand's public styling rather than downloaded from a single source, and some values were intentionally left messy or missing (padded whitespace, missing hash symbols, 3-digit shorthand, invalid and blank codes) to exercise the cleaning logic. A reference for the contrast formulas is the W3C WCAG guideline at https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html.

The purpose of this software is to practice a complete data pipeline in Python: load a CSV with Pandas, normalize and validate it, compute the exact WCAG contrast ratio between each brand's primary and background colors, and chart the findings with Matplotlib, including which brands meet the 4.5:1 minimum.

[Software Demo Video](https://drive.google.com/file/d/1yrhxS9leAcaCa1kOrnPdtoqLWBCBuD-c/view?usp=sharing)

# Data Analysis Results

Of the 26 rows, 3 were dropped during cleaning (one had no background color, one had no primary color, and one had an invalid hex code), leaving 23 brands.

* How common is each typography class? Sans-Serif dominates with 16 brands, followed by Serif with 5 and Monospace with 2.
* How many brands meet the WCAG AA 4.5:1 contrast minimum? 14 of the 23 brands pass and 9 fail.
* Which brands fail? Netflix (4.38), Airbnb (3.05), Stripe (3.31), Twitch (4.15), Snapchat (1.10), Bumble (1.57), Lyft (3.50), Linear (4.24), and Substack (2.91).
* Which brands have the strongest contrast? Medium and Vercel reach the maximum of 21.0:1, followed by NYTimes at 18.73.
* Does typography class relate to contrast? Serif brands averaged 13.87:1, Monospace 11.55:1, and Sans-Serif 7.58:1, though the Serif and Monospace groups are small samples.

# Development Environment

Tools used: Python, Pandas, Matplotlib, and VS Code / Antigravity.

Programming language: Python 3, with the Pandas and Matplotlib libraries.

# Useful Websites

* [Pandas Documentation](https://pandas.pydata.org/docs/)
* [Matplotlib Documentation](https://matplotlib.org/stable/index.html)
* [WCAG Contrast Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)

# Future Work

* Replace the hand-entered sample with colors extracted directly from brand websites.
* Add the stricter 7:1 AAA threshold and the 3:1 threshold for large text.
* Expand the data set so conclusions about typography class are statistically meaningful.
