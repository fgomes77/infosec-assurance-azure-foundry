const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
        Header, Footer, AlignmentType, LevelFormat, HeadingLevel, 
        BorderStyle, WidthType, ShadingType, PageNumber, VerticalAlign } = require('docx');
const fs = require('fs');

// Colors
const EURONEXT_TEAL = "008D7F";
const LIGHT_GRAY = "F0F0F0";
const MEDIUM_GRAY = "CCCCCC";

const border = { style: BorderStyle.SINGLE, size: 1, color: MEDIUM_GRAY };
const borders = { top: border, bottom: border, left: border, right: border };

// Calculate due date (2 months from now)
const today = new Date();
const dueDate = new Date(today.setMonth(today.getMonth() + 2));
const dueDateStr = dueDate.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' });

// Risk and Control Data extracted from Oracle Portugal PDF V2
const risksWithControls = [
    { 
        title: "BCM Exercising and Testing Absence",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Perform Automated Backups", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Protect Recovery Data", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Establish and Maintain an Isolated Instance of Recovery Data", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Test Data Recovery", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Sharing of Risk & BCM requirements with ICT-Third Party", status: "Implemented", responsible: "Euronext NV" }
        ]
    },
    { 
        title: "Change Control Program Absence",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Securely Manage Enterprise Assets and Software", status: "Implemented", responsible: "Oracle Portugal" }
        ]
    },
    { 
        title: "Remote Desktop Support Awareness Policy Absence",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Train Workforce Members to Recognize Social Engineering Attacks", status: "Implemented", responsible: "Oracle Portugal" }
        ]
    },
    { 
        title: "Weak Access Controls and Vulnerabilities",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Restrict Administrator Privileges to Dedicated Administrator Accounts", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Integration of System in IAM user lifecycle management and PAM tools", status: "Implemented", responsible: "Euronext NV" }
        ]
    },
    { 
        title: "IDS/IPS Signature Updates Absence",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Deploy a Network Intrusion Prevention Solution", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Integration of System in SOC logging and monitoring tools", status: "Implemented", responsible: "Euronext NV" }
        ]
    },
    { 
        title: "Software and Systems Inventory Absence",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Establish and Maintain a Software Inventory", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Integration or update of System in CMDB", status: "Implemented", responsible: "Euronext NV" }
        ]
    },
    { 
        title: "Supplier Services Tracking Deficiency",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Establish and Maintain an Inventory of Service Providers", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Establish and Maintain a Service Provider Management Policy", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Classify Service Providers", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Ensure Service Provider Contracts Include Security Requirements", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Assess Service Providers", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Monitor Service Providers", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Securely Decommission Service Providers", status: "Implemented", responsible: "Oracle Portugal" }
        ]
    },
    { 
        title: "Data Classification and Mapping Absence",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Establish and Maintain a Data Management Process", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Enforce Data Retention", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Securely Dispose of Data", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Encrypt Data on End-User Devices", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Establish and Maintain a Data Classification Scheme", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Document Data Flows", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Encrypt Data on Removable Media", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Encrypt Sensitive Data in Transit", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Encrypt Sensitive Data at Rest", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Segment Data Processing and Storage Based on Sensitivity", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Deploy a Data Loss Prevention Solution", status: "Implemented", responsible: "Oracle Portugal" }
        ]
    },
    { 
        title: "Supplier Risk Monitoring Deficiency",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Monitoring, Review and Change Management of Supplier Services", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Sharing of Compliance requirements with ICT-Third Party", status: "Implemented", responsible: "Euronext NV" },
            { name: "Sharing of Risk & BCM requirements with ICT-Third Party", status: "Implemented", responsible: "Euronext NV" }
        ]
    },
    { 
        title: "Inadequate Logging and Monitoring",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Designate Personnel to Manage Incident Handling", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Establish and Maintain Contact Information for Reporting Security Incidents", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Establish and Maintain an Enterprise Process for Reporting Incidents", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Establish and Maintain an Incident Response Process", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Assign Key Roles and Responsibilities", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Define Mechanisms for Communicating During Incident Response", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Conduct Routine Incident Response Exercises", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Conduct Post-Incident Reviews", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Establish and Maintain Security Incident Thresholds", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Integration of System in SOC logging and monitoring tools", status: "Implemented", responsible: "Euronext NV" }
        ]
    },
    { 
        title: "Supply Chain Cybersecurity Integration Gap",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Sharing of Compliance requirements with ICT-Third Party", status: "Implemented", responsible: "Euronext NV" },
            { name: "Sharing of Finance requirements with ICT-Third Party", status: "Implemented", responsible: "Euronext NV" },
            { name: "Sharing of Privacy requirements with ICT-Third Party", status: "Implemented", responsible: "Euronext NV" },
            { name: "Sharing of Risk & BCM requirements with ICT-Third Party", status: "Implemented", responsible: "Euronext NV" },
            { name: "Sharing of cyber security requirements with ICT-Third Party", status: "Implemented", responsible: "Euronext NV" }
        ]
    },
    { 
        title: "Legal and Regulatory Compliance Management",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Policies for Information Security", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Legal, Statutory, Regulatory and Contractual Requirements", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Sharing of Compliance requirements with ICT-Third Party", status: "Implemented", responsible: "Euronext NV" },
            { name: "Sharing of Privacy requirements with ICT-Third Party", status: "Implemented", responsible: "Euronext NV" }
        ]
    },
    { 
        title: "Cybersecurity Training for Specialized Roles",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Establish and Maintain a Security Awareness Program", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Train Workforce Members to Recognize Social Engineering Attacks", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Train Workforce Members on Authentication Best Practices", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Train Workforce on Data Handling Best Practices", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Train Workforce Members on Recognizing and Reporting Security Incidents", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Train Workforce on How to Identify and Report Missing Security Updates", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Train Workforce on Dangers of Insecure Networks", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Conduct Role-Specific Security Awareness and Skills Training", status: "Implemented", responsible: "Oracle Portugal" }
        ]
    },
    { 
        title: "Risk Response Planning and Communication",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Conduct Threat Modeling", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Sharing of Risk & BCM requirements with ICT-Third Party", status: "Implemented", responsible: "Euronext NV" },
            { name: "Sharing of cyber security requirements with ICT-Third Party", status: "Implemented", responsible: "Euronext NV" }
        ]
    },
    { 
        title: "SDLC Policies and Procedures Absence",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Establish and Maintain a Secure Application Development Process", status: "Implemented", responsible: "Oracle Portugal" }
        ]
    },
    { 
        title: "Security Test Findings Not Actioned",
        inherentRisk: "12-Medium",
        residualRisk: "4-Low",
        controls: [
            { name: "Validate Security Measures", status: "Implemented", responsible: "Oracle Portugal" },
            { name: "Review of Penetration test/vulnerability report", status: "Implemented", responsible: "Euronext NV" },
            { name: "Integration in CTI continuous monitoring activities", status: "Implemented", responsible: "Euronext NV" }
        ]
    },
];

function createHeaderCell(text, width) {
    return new TableCell({
        borders,
        width: { size: width, type: WidthType.DXA },
        shading: { fill: EURONEXT_TEAL, type: ShadingType.CLEAR },
        margins: { top: 40, bottom: 40, left: 60, right: 60 },
        verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({ 
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 16 })]
        })]
    });
}

function createCell(text, width, fill = null, bold = false, size = 14, align = AlignmentType.LEFT) {
    return new TableCell({
        borders,
        width: { size: width, type: WidthType.DXA },
        shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
        margins: { top: 30, bottom: 30, left: 60, right: 60 },
        verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({ 
            alignment: align,
            children: [new TextRun({ text, size, bold })]
        })]
    });
}

function createMergedCell(text, width, rowSpan, fill = null, bold = false, size = 14) {
    return new TableCell({
        borders,
        width: { size: width, type: WidthType.DXA },
        rowSpan: rowSpan,
        shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
        margins: { top: 30, bottom: 30, left: 60, right: 60 },
        verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({ 
            children: [new TextRun({ text, size, bold })]
        })]
    });
}

function createCardCell(label, value, width, valueColor = null, valueBold = true) {
    return new TableCell({
        borders,
        width: { size: width, type: WidthType.DXA },
        shading: { fill: LIGHT_GRAY, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 100, right: 100 },
        verticalAlign: VerticalAlign.CENTER,
        children: [
            new Paragraph({ 
                alignment: AlignmentType.CENTER,
                spacing: { after: 60 },
                children: [new TextRun({ text: label, size: 14, color: "666666" })]
            }),
            new Paragraph({ 
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: value, size: 28, bold: valueBold, color: valueColor || "000000" })]
            })
        ]
    });
}

function getStatusColor(status) {
    if (status === "Implemented") return "C6EFCE";
    if (status === "Pending") return "FFEB9C";
    if (status === "Not Doing") return "FFC7CE";
    return null;
}

function getDueDate(status) {
    if (status === "Pending") return dueDateStr;
    return "N/A";
}

// Calculate statistics
let totalControls = 0;
let implementedControls = 0;
let pendingControls = 0;
let notDoingControls = 0;

risksWithControls.forEach(risk => {
    risk.controls.forEach(ctrl => {
        totalControls++;
        if (ctrl.status === "Implemented") implementedControls++;
        else if (ctrl.status === "Pending") pendingControls++;
        else if (ctrl.status === "Not Doing") notDoingControls++;
    });
});

const totalRisks = risksWithControls.length;

// Build the main control table rows - NO Control ID column, NO Risk ID column
const controlTableRows = [];

controlTableRows.push(
    new TableRow({ 
        tableHeader: true,
        children: [
            createHeaderCell("Inherent", 900),
            createHeaderCell("Residual", 900),
            createHeaderCell("Risk Title", 2400),
            createHeaderCell("Control Name", 3200),
            createHeaderCell("Responsible", 1200),
            createHeaderCell("Status", 900),
            createHeaderCell("Due Date", 900),
        ]
    })
);

risksWithControls.forEach(risk => {
    risk.controls.forEach((ctrl, idx) => {
        const row = new TableRow({
            children: [
                ...(idx === 0 ? [
                    createMergedCell(risk.inherentRisk, 900, risk.controls.length, "FFEB9C", true, 10),
                    createMergedCell(risk.residualRisk, 900, risk.controls.length, "C6EFCE", true, 10),
                    createMergedCell(risk.title, 2400, risk.controls.length, LIGHT_GRAY, true, 10),
                ] : []),
                createCell(ctrl.name, 3200, null, false, 9),
                createCell(ctrl.responsible, 1200, null, false, 9, AlignmentType.CENTER),
                createCell(ctrl.status, 900, getStatusColor(ctrl.status), true, 9, AlignmentType.CENTER),
                createCell(getDueDate(ctrl.status), 900, null, false, 9, AlignmentType.CENTER),
            ]
        });
        controlTableRows.push(row);
    });
});

// Determine implemented ISO 27001 domains based on control categories
const implementedDomains = [
    "Information Security Policies / processes",
    "Organization of information security", 
    "Human resources security",
    "Asset management",
    "Access control",
    "Cryptography",
    "Operations security",
    "Communications security",
    "System acquisition, development and maintenance",
    "Information security incident management",
    "Information security aspects of business continuity management",
    "Compliance"
];

const doc = new Document({
    styles: {
        default: { document: { run: { font: "Arial", size: 18 } } },
        paragraphStyles: [
            { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 24, bold: true, font: "Arial", color: EURONEXT_TEAL },
              paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 0 } },
        ]
    },
    sections: [{
        properties: {
            page: {
                size: { width: 11906, height: 16838 },
                margin: { top: 720, right: 720, bottom: 720, left: 720 }
            }
        },
        headers: {
            default: new Header({
                children: [new Paragraph({
                    alignment: AlignmentType.RIGHT,
                    children: [new TextRun({ text: "CONFIDENTIAL - Euronext NV", size: 14, color: "666666" })]
                })]
            })
        },
        footers: {
            default: new Footer({
                children: [new Paragraph({
                    alignment: AlignmentType.CENTER,
                    children: [
                        new TextRun({ text: "Page ", size: 14, color: "666666" }),
                        new TextRun({ children: [PageNumber.CURRENT], size: 14, color: "666666" }),
                        new TextRun({ text: " of ", size: 14, color: "666666" }),
                        new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 14, color: "666666" })
                    ]
                })]
            })
        },
        children: [
            // Title
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 160 },
                children: [new TextRun({ text: "InfoSec TPA Report for DPO Team", bold: true, size: 32, color: EURONEXT_TEAL })]
            }),
            
            // Supplier Info
            new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                columnWidths: [1800, 3400, 1800, 3400],
                rows: [
                    new TableRow({ children: [
                        createCell("Supplier:", 2200, LIGHT_GRAY, true),
                        createCell("Oracle Portugal - Sistemas de Informacao Lda.", 4800),
                        createCell("Assessment:", 2200, LIGHT_GRAY, true),
                        createCell("Annual Monitoring 2025", 4800),
                    ]}),
                    new TableRow({ children: [
                        createCell("Client:", 2200, LIGHT_GRAY, true),
                        createCell("EURONEXT NV", 4800),
                        createCell("Date:", 2200, LIGHT_GRAY, true),
                        createCell("21/01/2026 - 23/01/2026", 4800),
                    ]}),
                    new TableRow({ children: [
                        createCell("DORA Scope:", 2200, LIGHT_GRAY, true),
                        createCell("Yes - Critical/Important ICT Provider", 4800),
                        createCell("Certifications:", 2200, LIGHT_GRAY, true),
                        createCell("ISO 27001, SOC 2 Type 2", 4800),
                    ]}),
                ]
            }),

            // Section 1: Executive Summary
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("1. Executive Summary")] }),
            
            new Paragraph({
                spacing: { after: 100 },
                children: [
                    new TextRun({ text: "Security measures in place to protect identifiable information: ", bold: true, size: 16, color: EURONEXT_TEAL }),
                    new TextRun({ text: "The supplier demonstrates comprehensive security controls with all identified risks treated and residual risk reduced to Low.", size: 16 })
                ]
            }),

            // Card-style statistics table
            new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                columnWidths: [2600, 2600, 2600, 2600],
                rows: [
                    new TableRow({ children: [
                        createCardCell("Total Risks", totalRisks.toString(), 3500, EURONEXT_TEAL),
                        createCardCell("Total Controls", totalControls.toString(), 3500, EURONEXT_TEAL),
                        createCardCell("Implemented", `${implementedControls} (${Math.round(implementedControls/totalControls*100)}%)`, 3500, "008D7F"),
                        createCardCell("Pending / Not Doing", `${pendingControls + notDoingControls} (${Math.round((pendingControls+notDoingControls)/totalControls*100)}%)`, 3500, pendingControls + notDoingControls > 0 ? "C00000" : "008D7F"),
                    ]}),
                ]
            }),

            // Section 2: Risk and Control Table
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("2. Risk Register with Control Implementation Status")] }),
            
            new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                columnWidths: [3466, 3467, 3467],
                rows: [
                    new TableRow({ children: [
                        createCell("Implemented", 3466, "C6EFCE", true, 14, AlignmentType.CENTER),
                        createCell("Pending", 3467, "FFEB9C", true, 14, AlignmentType.CENTER),
                        createCell("Not Doing", 3467, "FFC7CE", true, 14, AlignmentType.CENTER),
                    ]}),
                ]
            }),

            new Paragraph({ spacing: { before: 80 }, children: [] }),

            new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                columnWidths: [900, 900, 2400, 3200, 1200, 900, 900],
                rows: controlTableRows
            }),

            // Section 3: InfoSec TPRM Conclusion
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("3. InfoSec TPRM Conclusion on Data Protection and Privacy")] }),

            new Paragraph({
                spacing: { after: 80 },
                children: [
                    new TextRun({ text: "The security controls implemented are: ", bold: true, size: 16 }),
                    ...implementedDomains.flatMap((domain, idx) => {
                        const items = [new TextRun({ text: domain, bold: true, size: 16 })];
                        if (idx < implementedDomains.length - 1) {
                            items.push(new TextRun({ text: "; ", size: 16 }));
                        } else {
                            items.push(new TextRun({ text: ".", size: 16 }));
                        }
                        return items;
                    })
                ]
            }),

            new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                columnWidths: [2600, 7800],
                rows: [
                    new TableRow({ children: [
                        createCell("Risk Rating:", 2600, LIGHT_GRAY, true),
                        createCell("LOW - All controls implemented, residual risk minimized", 7800, "C6EFCE", true),
                    ]}),
                ]
            }),

            new Paragraph({ spacing: { before: 100 }, children: [new TextRun({ text: "Approval: ", bold: true, size: 16 }), new TextRun({ text: "Francisco Gomes (Analyst) - Approved | Pedro Santos (Manager) - Approved", size: 16 })] }),

            // PAGE BREAK - Annexes (Single Page, Two Columns)
            new Paragraph({ pageBreakBefore: true }),

            // Annex Title
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 200 },
                children: [new TextRun({ text: "Annexes", bold: true, size: 28, color: EURONEXT_TEAL })]
            }),

            // Annex - Five-column table for Risks, Controls, Status, Responsible, Due Dates
            new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                columnWidths: [2000, 3200, 1600, 1600, 2000],
                rows: [
                    // Header row
                    new TableRow({
                        children: [
                            new TableCell({
                                borders,
                                width: { size: 2000, type: WidthType.DXA },
                                shading: { fill: EURONEXT_TEAL, type: ShadingType.CLEAR },
                                margins: { top: 60, bottom: 60, left: 60, right: 60 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ 
                                    alignment: AlignmentType.CENTER,
                                    children: [new TextRun({ text: "List of All Risks Identified", bold: true, color: "FFFFFF", size: 14 })]
                                })]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 3200, type: WidthType.DXA },
                                shading: { fill: EURONEXT_TEAL, type: ShadingType.CLEAR },
                                margins: { top: 60, bottom: 60, left: 60, right: 60 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ 
                                    alignment: AlignmentType.CENTER,
                                    children: [new TextRun({ text: "List of All Controls", bold: true, color: "FFFFFF", size: 14 })]
                                })]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 1600, type: WidthType.DXA },
                                shading: { fill: EURONEXT_TEAL, type: ShadingType.CLEAR },
                                margins: { top: 60, bottom: 60, left: 60, right: 60 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ 
                                    alignment: AlignmentType.CENTER,
                                    children: [new TextRun({ text: "List of all Status", bold: true, color: "FFFFFF", size: 14 })]
                                })]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 1600, type: WidthType.DXA },
                                shading: { fill: EURONEXT_TEAL, type: ShadingType.CLEAR },
                                margins: { top: 60, bottom: 60, left: 60, right: 60 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ 
                                    alignment: AlignmentType.CENTER,
                                    children: [new TextRun({ text: "List of all Responsable", bold: true, color: "FFFFFF", size: 14 })]
                                })]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 2000, type: WidthType.DXA },
                                shading: { fill: EURONEXT_TEAL, type: ShadingType.CLEAR },
                                margins: { top: 60, bottom: 60, left: 60, right: 60 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ 
                                    alignment: AlignmentType.CENTER,
                                    children: [new TextRun({ text: "List of All Due Dates", bold: true, color: "FFFFFF", size: 14 })]
                                })]
                            }),
                        ]
                    }),
                    // Content row
                    new TableRow({
                        children: [
                            // Risks column
                            new TableCell({
                                borders,
                                width: { size: 2000, type: WidthType.DXA },
                                margins: { top: 60, bottom: 60, left: 60, right: 60 },
                                verticalAlign: VerticalAlign.TOP,
                                children: risksWithControls.map((risk) => new Paragraph({
                                    spacing: { after: 60 },
                                    children: [new TextRun({ text: risk.title, size: 10 })]
                                }))
                            }),
                            // Controls column (unique)
                            new TableCell({
                                borders,
                                width: { size: 3200, type: WidthType.DXA },
                                margins: { top: 60, bottom: 60, left: 60, right: 60 },
                                verticalAlign: VerticalAlign.TOP,
                                children: (() => {
                                    const uniqueControls = [];
                                    const seen = new Set();
                                    risksWithControls.forEach(risk => {
                                        risk.controls.forEach(ctrl => {
                                            if (!seen.has(ctrl.name)) {
                                                seen.add(ctrl.name);
                                                uniqueControls.push({ name: ctrl.name, status: ctrl.status, responsible: ctrl.responsible });
                                            }
                                        });
                                    });
                                    return uniqueControls.map(ctrl => new Paragraph({
                                        spacing: { after: 50 },
                                        children: [new TextRun({ text: ctrl.name, size: 9 })]
                                    }));
                                })()
                            }),
                            // Status column
                            new TableCell({
                                borders,
                                width: { size: 1600, type: WidthType.DXA },
                                margins: { top: 60, bottom: 60, left: 60, right: 60 },
                                verticalAlign: VerticalAlign.TOP,
                                children: (() => {
                                    const statuses = [];
                                    const seen = new Set();
                                    risksWithControls.forEach(risk => {
                                        risk.controls.forEach(ctrl => {
                                            if (!seen.has(ctrl.name)) {
                                                seen.add(ctrl.name);
                                                statuses.push(new Paragraph({
                                                    spacing: { after: 50 },
                                                    alignment: AlignmentType.CENTER,
                                                    children: [new TextRun({ text: ctrl.status, size: 9, bold: true, color: ctrl.status === "Implemented" ? "008D7F" : ctrl.status === "Pending" ? "C00000" : "666666" })]
                                                }));
                                            }
                                        });
                                    });
                                    return statuses;
                                })()
                            }),
                            // Responsible column
                            new TableCell({
                                borders,
                                width: { size: 1600, type: WidthType.DXA },
                                margins: { top: 60, bottom: 60, left: 60, right: 60 },
                                verticalAlign: VerticalAlign.TOP,
                                children: (() => {
                                    const responsibles = [];
                                    const seen = new Set();
                                    risksWithControls.forEach(risk => {
                                        risk.controls.forEach(ctrl => {
                                            if (!seen.has(ctrl.name)) {
                                                seen.add(ctrl.name);
                                                responsibles.push(new Paragraph({
                                                    spacing: { after: 50 },
                                                    alignment: AlignmentType.CENTER,
                                                    children: [new TextRun({ text: ctrl.responsible, size: 9 })]
                                                }));
                                            }
                                        });
                                    });
                                    return responsibles;
                                })()
                            }),
                            // Due Dates column
                            new TableCell({
                                borders,
                                width: { size: 2000, type: WidthType.DXA },
                                margins: { top: 60, bottom: 60, left: 60, right: 60 },
                                verticalAlign: VerticalAlign.TOP,
                                children: (() => {
                                    const dueDates = [];
                                    const seen = new Set();
                                    risksWithControls.forEach(risk => {
                                        risk.controls.forEach(ctrl => {
                                            if (!seen.has(ctrl.name)) {
                                                seen.add(ctrl.name);
                                                const dueDate = getDueDate(ctrl.status);
                                                dueDates.push(new Paragraph({
                                                    spacing: { after: 50 },
                                                    alignment: AlignmentType.CENTER,
                                                    children: [new TextRun({ text: dueDate, size: 9, bold: true, color: dueDate === "N/A" ? "008D7F" : "C00000" })]
                                                }));
                                            }
                                        });
                                    });
                                    return dueDates;
                                })()
                            }),
                        ]
                    }),
                ]
            }),

            // PAGE BREAK - Annex 1: Privacy Issues & Risks
            new Paragraph({ pageBreakBefore: true }),

            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 120 },
                children: [new TextRun({ text: "Annex 1: Privacy Issues & Risks", bold: true, size: 24, color: EURONEXT_TEAL })]
            }),

            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 120 },
                shading: { fill: EURONEXT_TEAL, type: ShadingType.CLEAR },
                children: [new TextRun({ text: "IDENTIFIED PRIVACY ISSUES AND ASSOCIATED RISKS", bold: true, color: "FFFFFF", size: 16 })]
            }),

            new Paragraph({
                spacing: { after: 80 },
                children: [new TextRun({ text: "Please refer to annex 3 for more information", italic: true, size: 14 })]
            }),

            // Privacy Issues Table
            new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                columnWidths: [600, 2200, 600, 2200, 2200, 2200],
                rows: [
                    // Header row
                    new TableRow({
                        tableHeader: true,
                        children: [
                            createHeaderCell("REF", 600),
                            createHeaderCell("PRIVACY ISSUE", 2200),
                            createHeaderCell("RAG", 600),
                            createHeaderCell("RISKS TO INDIVIDUAL(S)", 2200),
                            createHeaderCell("COMPLIANCE RISK", 2200),
                            createHeaderCell("CORPORATE RISK", 2200),
                        ]
                    }),
                    // Subheader row
                    new TableRow({
                        children: [
                            createCell("#", 600, LIGHT_GRAY, false, 8, AlignmentType.CENTER),
                            createCell("Use assessment response to detail the privacy factor resulting in risk", 2200, LIGHT_GRAY, false, 8),
                            createCell("Inherent Risk Rating", 600, LIGHT_GRAY, false, 8, AlignmentType.CENTER),
                            createCell("Complete if risk impacts data subject(s) or put N/A if not applicable", 2200, LIGHT_GRAY, false, 8),
                            createCell("Complete if risk causes non-compliance or put N/A if not applicable", 2200, LIGHT_GRAY, false, 8),
                            createCell("Complete if risk impacts business or put N/A if not applicable", 2200, LIGHT_GRAY, false, 8),
                        ]
                    }),
                    // PR3 Data row
                    new TableRow({
                        children: [
                            new TableCell({
                                borders,
                                width: { size: 600, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "PR3", bold: true, size: 12 })] })]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 2200, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.TOP,
                                children: [
                                    new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "KEEPING THE PERSONAL DATA SAFE AND SECURE (analysis based on InfoSec assessment)", bold: true, size: 10 })] }),
                                    ...risksWithControls.map(risk => new Paragraph({
                                        spacing: { after: 40 },
                                        children: [new TextRun({ text: risk.title, size: 9 })]
                                    }))
                                ]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 600, type: WidthType.DXA },
                                shading: { fill: "FFEB9C", type: ShadingType.CLEAR },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [
                                    new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "6", bold: true, size: 14 })] }),
                                    new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "MEDIUM", bold: true, size: 10 })] })
                                ]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 2200, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ children: [new TextRun({ text: "Breach of articles 5, 24 and 32 of the GDPR", size: 10 })] })]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 2200, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ children: [new TextRun({ text: "Fines - article 83 of the GDPR", size: 10 })] })]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 2200, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ children: [new TextRun({ text: "Fines - article 83 of the GDPR", size: 10 })] })]
                            }),
                        ]
                    }),
                ]
            }),

            // PAGE BREAK - Annex 2: Proposed Risk Solutions
            new Paragraph({ pageBreakBefore: true }),

            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 120 },
                children: [new TextRun({ text: "Annex 2: Proposed Risk Solutions and Mitigating Actions", bold: true, size: 24, color: EURONEXT_TEAL })]
            }),

            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 120 },
                shading: { fill: EURONEXT_TEAL, type: ShadingType.CLEAR },
                children: [new TextRun({ text: "PROPOSED RISK SOLUTIONS AND MITIGATING ACTIONS", bold: true, color: "FFFFFF", size: 16 })]
            }),

            // Solutions Table
            new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                columnWidths: [600, 1800, 600, 4200, 1000, 1000, 800],
                rows: [
                    // Header row
                    new TableRow({
                        tableHeader: true,
                        children: [
                            createHeaderCell("REF", 600),
                            createHeaderCell("RISK", 1800),
                            new TableCell({
                                borders,
                                width: { size: 600, type: WidthType.DXA },
                                shading: { fill: "FFEB9C", type: ShadingType.CLEAR },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "RAG", bold: true, size: 12 })] })]
                            }),
                            createHeaderCell("SOLUTION/MITIGATING ACTIONS", 4200),
                            createHeaderCell("RESULT", 1000),
                            createHeaderCell("OUTCOME", 1000),
                            new TableCell({
                                borders,
                                width: { size: 800, type: WidthType.DXA },
                                shading: { fill: "C6EFCE", type: ShadingType.CLEAR },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "RAG", bold: true, size: 12 })] })]
                            }),
                        ]
                    }),
                    // Subheader row
                    new TableRow({
                        children: [
                            createCell("#", 600, LIGHT_GRAY, false, 8, AlignmentType.CENTER),
                            createCell("Risk to be mitigated", 1800, LIGHT_GRAY, false, 8),
                            createCell("Inherent Risk Rating", 600, LIGHT_GRAY, false, 8, AlignmentType.CENTER),
                            createCell("Detail corrective actions, solutions and mitigating controls that address the risk", 4200, LIGHT_GRAY, false, 8),
                            createCell("Reduced, Eliminated or Accepted", 1000, LIGHT_GRAY, false, 8),
                            createCell("Has the solution(s) reduced the risk enough to proceed with processing?", 1000, LIGHT_GRAY, false, 8),
                            createCell("Residual Risk Rating", 800, LIGHT_GRAY, false, 8, AlignmentType.CENTER),
                        ]
                    }),
                    // PR3 Data row with all unique controls
                    new TableRow({
                        children: [
                            new TableCell({
                                borders,
                                width: { size: 600, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "PR3", bold: true, size: 12 })] })]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 1800, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ children: [new TextRun({ text: "KEEPING THE PERSONAL DATA SAFE AND SECURE (analysis based on InfoSec assessment)", bold: true, size: 9 })] })]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 600, type: WidthType.DXA },
                                shading: { fill: "FFEB9C", type: ShadingType.CLEAR },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "6", bold: true, size: 14 })] })]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 4200, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.TOP,
                                children: (() => {
                                    const uniqueControls = [];
                                    const seen = new Set();
                                    risksWithControls.forEach(risk => {
                                        risk.controls.forEach(ctrl => {
                                            if (!seen.has(ctrl.name)) {
                                                seen.add(ctrl.name);
                                                uniqueControls.push(new Paragraph({
                                                    spacing: { after: 30 },
                                                    children: [new TextRun({ text: ctrl.name, size: 9 })]
                                                }));
                                            }
                                        });
                                    });
                                    return uniqueControls;
                                })()
                            }),
                            new TableCell({
                                borders,
                                width: { size: 1000, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Reduced", size: 10 })] })]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 1000, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "N/A", size: 10 })] })]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 800, type: WidthType.DXA },
                                shading: { fill: "C6EFCE", type: ShadingType.CLEAR },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [
                                    new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "4", bold: true, size: 14 })] }),
                                    new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "LOW", bold: true, size: 10 })] })
                                ]
                            }),
                        ]
                    }),
                ]
            }),

            // PAGE BREAK - Annex 3: Action Plan
            new Paragraph({ pageBreakBefore: true }),

            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 120 },
                children: [new TextRun({ text: "Annex 3: Action Plan", bold: true, size: 24, color: EURONEXT_TEAL })]
            }),

            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 120 },
                shading: { fill: EURONEXT_TEAL, type: ShadingType.CLEAR },
                children: [new TextRun({ text: "ACTION PLAN", bold: true, color: "FFFFFF", size: 16 })]
            }),

            // Action Plan Table
            new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                columnWidths: [800, 4400, 1600, 1600, 2000],
                rows: [
                    // Header row
                    new TableRow({
                        tableHeader: true,
                        children: [
                            createHeaderCell("REF", 800),
                            createHeaderCell("SOLUTION/MITIGATING ACTIONS", 4400),
                            createHeaderCell("OWNER", 1600),
                            createHeaderCell("STATUS", 1600),
                            createHeaderCell("DUE DATE", 2000),
                        ]
                    }),
                    // PR_3 Data row
                    new TableRow({
                        children: [
                            new TableCell({
                                borders,
                                width: { size: 800, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.CENTER,
                                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "PR_3", bold: true, size: 12 })] })]
                            }),
                            new TableCell({
                                borders,
                                width: { size: 4400, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.TOP,
                                children: (() => {
                                    const uniqueControls = [];
                                    const seen = new Set();
                                    risksWithControls.forEach(risk => {
                                        risk.controls.forEach(ctrl => {
                                            if (!seen.has(ctrl.name)) {
                                                seen.add(ctrl.name);
                                                uniqueControls.push(new Paragraph({
                                                    spacing: { after: 30 },
                                                    children: [new TextRun({ text: ctrl.name, size: 9 })]
                                                }));
                                            }
                                        });
                                    });
                                    return uniqueControls;
                                })()
                            }),
                            new TableCell({
                                borders,
                                width: { size: 1600, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.TOP,
                                children: (() => {
                                    const owners = [];
                                    const seen = new Set();
                                    risksWithControls.forEach(risk => {
                                        risk.controls.forEach(ctrl => {
                                            if (!seen.has(ctrl.name)) {
                                                seen.add(ctrl.name);
                                                owners.push(new Paragraph({
                                                    spacing: { after: 30 },
                                                    alignment: AlignmentType.CENTER,
                                                    children: [new TextRun({ text: ctrl.responsible, size: 9 })]
                                                }));
                                            }
                                        });
                                    });
                                    return owners;
                                })()
                            }),
                            new TableCell({
                                borders,
                                width: { size: 1600, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.TOP,
                                children: (() => {
                                    const statuses = [];
                                    const seen = new Set();
                                    risksWithControls.forEach(risk => {
                                        risk.controls.forEach(ctrl => {
                                            if (!seen.has(ctrl.name)) {
                                                seen.add(ctrl.name);
                                                statuses.push(new Paragraph({
                                                    spacing: { after: 30 },
                                                    alignment: AlignmentType.CENTER,
                                                    children: [new TextRun({ text: ctrl.status, size: 9, bold: true, color: ctrl.status === "Implemented" ? "008D7F" : ctrl.status === "Pending" ? "C00000" : "666666" })]
                                                }));
                                            }
                                        });
                                    });
                                    return statuses;
                                })()
                            }),
                            new TableCell({
                                borders,
                                width: { size: 2000, type: WidthType.DXA },
                                margins: { top: 40, bottom: 40, left: 40, right: 40 },
                                verticalAlign: VerticalAlign.TOP,
                                children: (() => {
                                    const dueDates = [];
                                    const seen = new Set();
                                    risksWithControls.forEach(risk => {
                                        risk.controls.forEach(ctrl => {
                                            if (!seen.has(ctrl.name)) {
                                                seen.add(ctrl.name);
                                                const dueDate = getDueDate(ctrl.status);
                                                dueDates.push(new Paragraph({
                                                    spacing: { after: 30 },
                                                    alignment: AlignmentType.CENTER,
                                                    children: [new TextRun({ text: dueDate, size: 9, bold: true, color: dueDate === "N/A" ? "008D7F" : "C00000" })]
                                                }));
                                            }
                                        });
                                    });
                                    return dueDates;
                                })()
                            }),
                        ]
                    }),
                ]
            }),
        ]
    }]
});

Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync("/mnt/user-data/outputs/InfoSec_TPA_Report_Oracle_Portugal_DPO_v2.docx", buffer);
    console.log("InfoSec TPA Report created successfully!");
    console.log(`Total Risks: ${totalRisks}`);
    console.log(`Total Controls: ${totalControls}`);
    console.log(`Implemented: ${implementedControls} (${Math.round(implementedControls/totalControls*100)}%)`);
    console.log(`Pending/Not Doing: ${pendingControls + notDoingControls} (${Math.round((pendingControls+notDoingControls)/totalControls*100)}%)`);
});
