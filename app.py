from flask import Flask, request, make_response
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def getroute():
    return "hello world"
@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        # Parse the JSON payload
        payload = request.get_json()
        project = payload.get("project", "Unnamed Project")
        client_name = payload.get("clientName", "Unknown Client")
        subworks = payload.get("subworks", [])

        # Generate content for each subwork
        subworks_html = ""
        grand_total = 0

        for idx, subwork in enumerate(subworks, start=1):
            name = subwork.get("name", "Unnamed Subwork")
            default_sft = subwork["default"].get("SFT", 0)
            default_cft = subwork["default"].get("CFT", 0)
            details = subwork.get("details", [])
            reductions = subwork.get("reductions", [])

            # Calculate total quantities for details and reductions
            details_rows = ""
            total_quantity = 0
            for count, d in enumerate(details, start=1):
                if default_sft > 0:
                    quantity = d['length'] * d['breadth'] * d['number']
                elif default_cft > 0:
                    quantity = d['length'] * d['breadth'] * d['depth'] * d['number']
                else:
                    quantity = 0  # Fallback if neither SFT nor CFT is provided
                total_quantity += quantity
                details_rows += f"<tr><td>{count}</td><td>{d['name']}</td><td>{d['number']}</td>" \
                                f"<td>{d['length']}</td><td>{d['breadth']}</td><td>{d['depth']}</td>" \
                                f"<td>{quantity}</td></tr>"

            reduction_quantity = 0
            reductions_rows = ""
            for count, r in enumerate(reductions, start=1):
                if default_sft > 0:
                    quantity = r['length'] * r['breadth'] * r['number']
                elif default_cft > 0:
                    quantity = r['length'] * r['breadth'] * r['depth'] * r['number']
                else:
                    quantity = 0
                reduction_quantity += quantity
                reductions_rows += f"<tr><td>{count}</td><td>{r['name']}</td><td>{r['number']}</td>" \
                                   f"<td>{r['length']}</td><td>{r['breadth']}</td><td>{r['depth']}</td>" \
                                   f"<td>{quantity}</td></tr>"

            # Calculate net quantity and total cost
            net_quantity = total_quantity - reduction_quantity
            rate=0
            if default_cft>0:
                rate=default_cft
            if default_sft>0:
                rate=default_sft
            # rate = 15 if default_sft > 0 else 18  # Example rates for SFT and CFT
            total_cost = net_quantity * rate
            grand_total += total_cost

            # Create subwork HTML
            subworks_html += f"""
            <h3>{idx}. {name}</h3>
            <p>Default SFT: {default_sft}, Default CFT: {default_cft}</p>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
                <thead>
                    <tr>
                        <th>S.No</th><th>Name</th><th>Number</th>
                        <th>Length(ft)</th><th>Breadth(ft)</th><th>Depth(ft)</th><th>Quantity</th>
                    </tr>
                </thead>
                <tbody>
                    {details_rows if details else '<tr><td colspan="7" style="text-align: center;">No details available</td></tr>'}
                </tbody>
            </table>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
                <thead>
                    <tr>
                        <th>S.No</th><th>Name</th><th>Number</th>
                        <th>Length(ft)</th><th>Breadth(ft)</th><th>Depth(ft)</th><th>Quantity</th>
                    </tr>
                </thead>
                <tbody>
                    {reductions_rows if reductions else '<tr><td colspan="7" style="text-align: center;">No reductions available</td></tr>'}
                </tbody>
            </table>
            <p>Total Quantity: {total_quantity}</p>

            <p> Deductions: <strong>{reduction_quantity}</strong></p>
            <p> Net Quantity: <strong>{net_quantity}</strong></p>
            <p>Total Cost: <strong>R.s {total_cost}</strong></p>
            """

        # Final HTML
        html_content = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th, td {{
                    border: 1px solid black;
                    padding: 5px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                h1, h3 {{
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <h1>{project}</h1>
            <span>ABC Company </span>
            <p><strong>Project Name:</strong> {project}</p>
            <p><strong>Client Name:</strong> {client_name}</p>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
            {subworks_html}
            <h2>Grand Total : R.s {grand_total}</h2>
        </body>
        </html>
        """

        # Convert HTML to PDF
        pdf = BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf)
        pdf.seek(0)

        if pisa_status.err:
            return {"error": "Error in PDF generation"}, 500

        # Send PDF as response
        response = make_response(pdf.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=report.pdf'
        return response

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
