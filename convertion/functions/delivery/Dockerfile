# Delivery Function App image — Python 3.11 Functions host + Node 20 (pptxgenjs,
# docx, mermaid-cli renderers) + Playwright Chromium (HTML->PDF/PNG, spider
# PNG, dashboard section screenshots) + poppler/tesseract (pdf-coverage) +
# ffmpeg (speaker clips). Built by `az acr build` into the private registry and
# deployed by infra/delivery.bicep (`deliveryImage`) on the Elastic Premium plan
# (a Flex Consumption Python app has no Node/Chromium). EU region, managed
# identity, no keys baked in.
#
# Image split (reviewed against ../office-tools/Dockerfile): LibreOffice,
# pandoc, qpdf and ImageMagick are deliberately NOT here — they belong to
# the office-tools app, which this app calls over OFFICE_TOOLS_BASE_URL for
# the xlsx recalc gate and format conversions. poppler + tesseract ARE here
# because the pdf-full-coverage-analyzer scripts run in THIS container
# (/api/pdf/{stage}); office-tools carries its own copies for the pdf-skill
# helpers. Nothing in this image needs defusedxml/lxml: OOXML validation is
# an office-tools endpoint. See ../office-tools/README.md and README.md
# §"Image split review".
FROM mcr.microsoft.com/azure-functions/python:4-python3.11

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    NODE_PATH=/home/site/wwwroot/node_modules \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates gnupg poppler-utils tesseract-ocr tesseract-ocr-eng tesseract-ocr-por \
        ffmpeg fonts-dejavu fonts-liberation \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /home/site/wwwroot/requirements.txt
RUN pip install --no-cache-dir -r /home/site/wwwroot/requirements.txt \
    && playwright install --with-deps chromium

# Node dependencies shared by every staged renderer (pptxgenjs, docx, mermaid-cli)
COPY package.json package-lock.json /home/site/wwwroot/
# mermaid-cli drives its own puppeteer browser: install it as part of the
# BUILD and let the build fail if it cannot be fetched — a silently skipped
# download used to surface only when the first diagram render failed in
# production.
RUN cd /home/site/wwwroot && npm ci --omit=dev --ignore-scripts \
    && npx --yes puppeteer browsers install chrome-headless-shell

# Function code + renderers/ (staged by ../../scripts/stage_renderers.py BEFORE the build)
COPY . /home/site/wwwroot
RUN for d in /home/site/wwwroot/renderers/*/; do \
        if [ -f "$d/package.json" ]; then (cd "$d" && npm ci --omit=dev --ignore-scripts 2>/dev/null || npm install --omit=dev --ignore-scripts); fi; \
    done \
    && find /home/site/wwwroot -name "__pycache__" -type d -prune -exec rm -rf {} + \
    && python3 -c "import playwright, docx, pptx, openpyxl, fitz, pdfplumber; print('image ok')"
