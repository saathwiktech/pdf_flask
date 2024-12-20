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
        payload = request.get_json()
        project = payload.get("project", "Unnamed Project")
        client_name = payload.get("clientName", "Unknown Client")
        subworks = payload.get("subworks", [])

        subworks_html = ""
        grand_total = 0

        for idx, subwork in enumerate(subworks, start=1):
            name = subwork.get("name", "Unnamed Subwork")
            default_sft = subwork["default"].get("SFT", 0)
            default_cft = subwork["default"].get("CFT", 0)
            details = subwork.get("details", [])
            reductions = subwork.get("reductions", [])

            details_rows = ""
            total_quantity = 0
            r=0
            for count, d in enumerate(details, start=1):
                if default_sft > 0:
                    r=default_sft
                    quantity = d['length'] * d['breadth'] * d['number']
                elif default_cft > 0:
                    r=default_cft
                    quantity = d['length'] * d['breadth'] * d['depth'] * d['number']
                else:
                    quantity = 0  
                total_quantity += quantity
                details_rows += f"<tr><td>{count}</td><td>{d['name']}</td><td>{d['number']}</td>" \
                                f"<td>{d['length']}</td><td>{d['breadth']}</td><td>{d['depth']}</td>" \
                                f"<td>{quantity:.2f}</td><td>-</td><td>-</td></tr>"                                
            details_rows += f"<tr><td colspan='6' style='text-align: center;'>-</td>" \
                   f"<td>{total_quantity:.2f}</td><td>{r}</td><td><strong>R.s {total_quantity * r:.2f}</strong></td></tr>"

            reduction_quantity = 0
            reductions_rows = ""
            rr=0
            for count, r in enumerate(reductions, start=1):
                if default_sft > 0:
                    rr=default_sft
                    quantity = r['length'] * r['breadth'] * r['number']
                elif default_cft > 0:
                    rr=default_cft
                    quantity = r['length'] * r['breadth'] * r['depth'] * r['number']
                else:
                    quantity = 0
                reduction_quantity += quantity
                reductions_rows += f"<tr><td>{count}</td><td>{r['name']}</td><td>{r['number']}</td>" \
                                   f"<td>{r['length']}</td><td>{r['breadth']}</td><td>{r['depth']}</td>" \
                                   f"<td>{quantity:.2f}</td><td>-</td><td>-</td></tr>"
            reductions_rows += f"<tr><td colspan='6' style='text-align: center;'>-</td>" \
                   f"<td>{reduction_quantity:.2f}</td><td>{rr}</td><td><strong>R.s {reduction_quantity * rr:.2f}</strong></td></tr>"

            
            
            net_quantity = total_quantity - reduction_quantity
            rate=0
            if default_cft>0:
                rate=default_cft
            if default_sft>0:
                rate=default_sft
           
            total_cost = net_quantity * rate
            grand_total += total_cost
            
            subworks_html += f"""
            <h3>{idx}. {name}</h3>
            <p>Default SFT: {default_sft}, Default CFT: {default_cft}</p>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
                <thead>
                    <tr>
                        <th>S.No</th><th>Name</th><th>Number</th>
                        <th>Length(ft)</th><th>Breadth(ft)</th><th>Depth(ft)</th><th>Quantity</th><th>Unit/Rate</th><th>Amount (Rs.)</th>
                    </tr>
                </thead>
                <tbody>
                    {details_rows if details else '<tr><td colspan="9" style="text-align: center;">No details available</td></tr>'}
                </tbody>
            </table>
            <div>Deduction Table</div>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
                <thead>
                    <tr>
                        <th>S.No</th><th>Name</th><th>Number</th>
                        <th>Length(ft)</th><th>Breadth(ft)</th><th>Depth(ft)</th><th>Quantity</th><th>Unit/Rate</th><th>Amount(Rs.)</th>
                    </tr>
                </thead>
                <tbody>
                    {reductions_rows if reductions else '<tr><td colspan="9" style="text-align: center;">No reductions available</td></tr>'}
                </tbody>
            </table>
            <p>Total Quantity: {total_quantity:.2f}</p>

            <p> Deductions: <strong>{reduction_quantity:.2f}</strong></p>
            <p> Net Quantity: <strong>{net_quantity:.2f}</strong></p>
            <p>Total Cost: <strong>Rs. {total_cost:.2f}</strong></p>
            """

      
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
            <h2>Grand Total :<strong> Rs. {grand_total:.2f}</strong></h2>
        </body>
        </html>
        """

        
        pdf = BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf)
        pdf.seek(0)

        if pisa_status.err:
            return {"error": "Error in PDF generation"}, 500

        
        response = make_response(pdf.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=report.pdf'
        return response

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
