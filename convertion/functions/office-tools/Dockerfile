# office-tools Function App image — Python 3.11 Functions host + LibreOffice
# (soffice) + pandoc + poppler + qpdf + tesseract + ImageMagick: the binary
# toolchain the docx/pptx/xlsx/pdf skills assume and that Foundry
# code_interpreter does not have.
#
# Deliberately SEPARATE from functions/delivery (see that Dockerfile and
# ../../infra/delivery.bicep): delivery carries Node 20 + Playwright/Chromium
# and holds the SharePoint write identity; LibreOffice roughly doubles an
# image, needs a writable profile directory and is the widest attack surface
# here, so it runs in its own container with NO Azure credential and no
# outbound network. Built by `az acr build` into the private registry and
# deployed by infra/delivery.bicep (`officeToolsImage`) on the same Elastic
# Premium plan. EU region, managed identity for the pull only, no keys baked in.
#
# Build order (toolchain/ MUST be staged first — it is the byte-verified skill
# code, not part of the repo):
#   python3 stage_toolchain.py
#   az acr build -r {registry} -t infosec-office-tools:{tag} .
FROM mcr.microsoft.com/azure-functions/python:4-python3.11

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true \
    HOME=/tmp \
    SAL_USE_VCLPLUGIN=svp \
    SAL_DISABLE_OPENCL=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# libreoffice-{writer,calc,impress}: DOCX/XLSX/PPTX conversion + the
#   calculateAll() macro recalc.py drives.
# pandoc: markdown/HTML <-> DOCX. poppler-utils: pdftoppm/pdftotext page
#   rasterisation. qpdf: linearise/repair. tesseract (eng+por): the OCR the
#   pdf skill's helpers expect locally — scanned evidence still goes to
#   Document Intelligence through the delivery Function (/api/extract_pdf).
# imagemagick: image ops of the skills' visual-QA steps.
# gcc/libc6-dev: office/soffice.py compiles a tiny AF_UNIX shim at runtime
#   when the sandbox blocks unix sockets (byte-verified script, do not remove).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-core libreoffice-writer libreoffice-calc libreoffice-impress \
        libreoffice-common fonts-dejavu fonts-liberation fonts-noto-core \
        pandoc poppler-utils qpdf ghostscript imagemagick \
        tesseract-ocr tesseract-ocr-eng tesseract-ocr-por \
        gcc libc6-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /home/site/wwwroot/requirements.txt
RUN pip install --no-cache-dir -r /home/site/wwwroot/requirements.txt

# Function code + toolchain/ (staged by ./stage_toolchain.py BEFORE the build)
COPY . /home/site/wwwroot

RUN find /home/site/wwwroot -name "__pycache__" -type d -prune -exec rm -rf {} + \
    && soffice --headless --version \
    && pandoc --version | head -1 \
    && pdftoppm -v 2>&1 | head -1 \
    && python3 -c "import openpyxl, docx, pptx, pypdf, defusedxml, PIL, jsonschema; print('image ok')"
