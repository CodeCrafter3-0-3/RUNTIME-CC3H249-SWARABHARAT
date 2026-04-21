Exporting Slide Deck to PDF

You can export `docs/slide_deck.html` to PDF using headless Chrome or your browser's Print → Save as PDF.

Headless (Chromium) example:

```bash
# Using Puppeteer or chrome headless
google-chrome --headless --disable-gpu --print-to-pdf=slides.pdf file:///$PWD/docs/slide_deck.html
```

Or open `docs/slide_deck.html` in Chrome and Print → Save as PDF (set page size to A4/Letter and scale to fit).
