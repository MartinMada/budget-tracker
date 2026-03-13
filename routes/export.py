from flask import Blueprint, make_response, request
from flask_login import login_required, current_user
from database import db
from models import Transaction
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime

export_bp = Blueprint('export', __name__)

@export_bp.route('/api/export/pdf', methods=['GET'])
@login_required
def export_pdf():
    month = request.args.get('month', '')

    # Ambil transaksi user
    query = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date.desc())

    if month:
        try:
            year, mon = month.split('-')
            query = query.filter(
                db.extract('year',  Transaction.date) == int(year),
                db.extract('month', Transaction.date) == int(mon)
            )
        except ValueError:
            pass

    transactions = query.all()

    # Hitung ringkasan
    total_income  = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    balance       = total_income - total_expense

    # ── Generate PDF ──────────────────────────────────────────
    buffer = BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    styles   = getSampleStyleSheet()
    elements = []

    # ── Header ──
    title_style = ParagraphStyle(
        'Title',
        parent    = styles['Title'],
        fontSize  = 20,
        textColor = colors.HexColor('#00ffb4'),
        spaceAfter= 4
    )
    sub_style = ParagraphStyle(
        'Sub',
        parent    = styles['Normal'],
        fontSize  = 10,
        textColor = colors.HexColor('#6aaa88'),
        spaceAfter= 2,
        alignment = TA_CENTER
    )

    elements.append(Paragraph("PROSPR", title_style))

    label = f"Laporan Keuangan — {current_user.username}"
    if month:
        try:
            dt = datetime.strptime(month, '%Y-%m')
            label += f" — {dt.strftime('%B %Y')}"
        except ValueError:
            pass
    elements.append(Paragraph(label, sub_style))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
        sub_style
    ))
    elements.append(Spacer(1, 6*mm))

    # ── Ringkasan ──
    def fmt(amount):
        return f"Rp {amount:,.0f}".replace(',', '.')

    summary_data = [
        ['Total Pemasukan', 'Total Pengeluaran', 'Saldo Bersih'],
        [fmt(total_income), fmt(total_expense), fmt(balance)]
    ]

    summary_table = Table(summary_data, colWidths=[55*mm, 55*mm, 55*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,0), colors.HexColor('#0d0d1a')),
        ('BACKGROUND',  (0,1), (0,1),  colors.HexColor('#0a1a12')),
        ('BACKGROUND',  (1,1), (1,1),  colors.HexColor('#1a0a12')),
        ('BACKGROUND',  (2,1), (2,1),
            colors.HexColor('#0a1a12') if balance >= 0 else colors.HexColor('#1a0a12')),
        ('TEXTCOLOR',   (0,0), (-1,0), colors.HexColor('#6aaa88')),
        ('TEXTCOLOR',   (0,1), (0,1),  colors.HexColor('#00ffb4')),
        ('TEXTCOLOR',   (1,1), (1,1),  colors.HexColor('#ff00aa')),
        ('TEXTCOLOR',   (2,1), (2,1),
            colors.HexColor('#00ffb4') if balance >= 0 else colors.HexColor('#ff00aa')),
        ('FONTNAME',    (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,0),  9),
        ('FONTSIZE',    (0,1), (-1,1),  12),
        ('ALIGN',       (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('BOX',         (0,0), (-1,-1), 1, colors.HexColor('#00ffb4')),
        ('INNERGRID',   (0,0), (-1,-1), 0.5, colors.HexColor('#1a3a2a')),
        ('TOPPADDING',  (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0),(-1,-1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 6*mm))

    # ── Tabel Transaksi ──
    header = ['Tanggal', 'Judul', 'Kategori', 'Tipe', 'Nominal']
    rows   = [header]

    for t in transactions:
        rows.append([
            t.date.strftime('%d/%m/%Y'),
            t.title[:35] + ('...' if len(t.title) > 35 else ''),
            t.category,
            'Pemasukan' if t.type == 'income' else 'Pengeluaran',
            fmt(t.amount)
        ])

    if not transactions:
        rows.append(['—', 'Tidak ada transaksi', '—', '—', '—'])

    tx_table = Table(rows, colWidths=[28*mm, 62*mm, 32*mm, 28*mm, 35*mm])
    tx_style = TableStyle([
        # Header
        ('BACKGROUND',   (0,0), (-1,0),  colors.HexColor('#0d0d1a')),
        ('TEXTCOLOR',    (0,0), (-1,0),  colors.HexColor('#00ffb4')),
        ('FONTNAME',     (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,0),  9),
        ('ALIGN',        (0,0), (-1,0),  'CENTER'),
        ('TOPPADDING',   (0,0), (-1,0),  7),
        ('BOTTOMPADDING',(0,0), (-1,0),  7),
        # Data rows
        ('FONTNAME',     (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',     (0,1), (-1,-1), 8),
        ('TOPPADDING',   (0,1), (-1,-1), 5),
        ('BOTTOMPADDING',(0,1), (-1,-1), 5),
        ('TEXTCOLOR',    (0,1), (-1,-1), colors.HexColor('#b0ffd8')),
        # Alternating rows
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [
            colors.HexColor('#080810'),
            colors.HexColor('#0d0d1a')
        ]),
        # Nominal column
        ('ALIGN',        (4,0), (4,-1),  'RIGHT'),
        # Border
        ('BOX',          (0,0), (-1,-1), 1, colors.HexColor('#00ffb4')),
        ('INNERGRID',    (0,0), (-1,-1), 0.3, colors.HexColor('#1a3a2a')),
    ])

    # Warnai baris income/expense
    for i, t in enumerate(transactions, start=1):
        if t.type == 'income':
            tx_style.add('TEXTCOLOR', (4,i), (4,i), colors.HexColor('#00ffb4'))
        else:
            tx_style.add('TEXTCOLOR', (4,i), (4,i), colors.HexColor('#ff00aa'))

    tx_table.setStyle(tx_style)
    elements.append(tx_table)
    elements.append(Spacer(1, 8*mm))

    # ── Footer ──
    footer_style = ParagraphStyle(
        'Footer',
        parent    = styles['Normal'],
        fontSize  = 8,
        textColor = colors.HexColor('#4a7a66'),
        alignment = TA_CENTER
    )
    elements.append(Paragraph(
        f"Prospr • {current_user.username} • {datetime.now().strftime('%d/%m/%Y')}",
        footer_style
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    # Return sebagai file download
    filename = f"prospr_{current_user.username}"
    if month:
        filename += f"_{month}"
    filename += ".pdf"

    response = make_response(buffer.read())
    response.headers['Content-Type']        = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response