import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
from LOG.reports import DATABASE_VALIDATIONS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_validation(engine, validation):
    """Executa uma validação SQL. Retorna um DataFrame para multi-linhas ou um dict para linha única."""
    validation_name = validation['name']
    query = validation['query']
    is_multi_row = validation.get('multi_row', False) 
    status_col = validation['status_check_column']
    
    try:
        logging.info(f"Executing: {validation_name} (Multi-Row: {is_multi_row})")
        
        with engine.connect() as connection:
            result_proxy = connection.execute(text(query))
            df = pd.DataFrame(result_proxy.all(), columns=result_proxy.keys())
            
            if df.empty:
                logging.warning(f"Validation {validation_name} returned no rows.")
                return {
                    "name": validation_name,
                    "description": validation['description'],
                    "status": "ERROR",
                    "details": pd.DataFrame({"Error": ["Query retornou 0 linhas."]}),
                    "status_check_column": status_col,
                    "multi_row": is_multi_row,
                }

            if is_multi_row:
                df[status_col] = df[status_col].astype(str).str.upper()
                status_counts = df[status_col].value_counts().to_dict()
                
                if 'FALSE' in status_counts and 'TRUE' in status_counts:
                    final_status = "WARNING"
                elif 'FALSE' in status_counts:
                    final_status = "FALSE"
                else:
                    final_status = "TRUE"
                
                details = df 
            else:
                result_dict = df.iloc[0].to_dict()
                final_status = str(result_dict.get(status_col, 'UNKNOWN')).upper()
                details = result_dict
            
            logging.info(f"Result for {validation_name}: Final Status={final_status}")
            
            return {
                "name": validation_name,
                "description": validation['description'],
                "status": final_status,
                "details": details,
                "multi_row": is_multi_row,
                "status_check_column": status_col,
            }

    except Exception as e:
        logging.error(f"Error executing validation {validation_name}: {e}")
        return {
            "name": validation_name,
            "description": validation['description'],
            "status": "ERROR",
            "details": {"Error": str(e)},
            "multi_row": is_multi_row,
            "status_check_column": status_col,
        }

def create_report_html(results):
    """Generates a structured, visually modern HTML body for the email."""
    
    CSS_STYLE = """
    <style>
        body { font-family: 'Arial', sans-serif; background-color: #f4f4f4; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: auto; background: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); }
        h1 { color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 25px; }
        .log-entry { border: 1px solid #ddd; border-radius: 5px; margin-bottom: 15px; padding: 15px; background-color: #fff; }
        .status-TRUE { background-color: #e6ffe6; border-left: 5px solid #28a745; } 
        .status-FALSE { background-color: #ffe6e6; border-left: 5px solid #dc3545; }
        .status-ERROR { background-color: #fff0b3; border-left: 5px solid #ffc107; }
        .status-label { font-weight: bold; margin-right: 10px; padding: 3px 8px; border-radius: 3px; }
        .label-TRUE { color: #28a745; background-color: #d4edda; }
        .label-FALSE { color: #dc3545; background-color: #f8d7da; }
        .label-ERROR { color: #ffc107; background-color: #fff3cd; }
        .details-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        .details-table th, .details-table td { border: 1px solid #eee; padding: 8px; text-align: left; }
        .details-table th { background-color: #f8f9fa; }
        .error-section { margin-top: 20px; padding: 15px; border: 2px dashed #dc3545; background-color: #f8d7da; color: #dc3545; border-radius: 5px; }
        .status-WARNING { background-color: #fffae6; border-left: 5px solid #ffc107; }
        .label-WARNING { color: #ffc107; background-color: #fff3cd; }
        .details-table { 
            width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9em; 
            overflow-x: auto; display: block; 
        }
        .details-table th, .details-table td { 
            border: 1px solid #eee; padding: 8px; text-align: left; 
            white-space: nowrap; 
        }
        .details-table th { background-color: #f8f9fa; }
        .details-table .status-FALSE-cell { background-color: #f8d7da; font-weight: bold; } 
        .details-table .status-TRUE-cell { background-color: #d4edda; }
        .error-section { margin-top: 20px; padding: 15px; border: 2px dashed #dc3545; background-color: #f8d7da; color: #dc3545; border-radius: 5px; }
    </style>
    """
    
    errors = [r for r in results if r['status'] != 'TRUE']
    successes = [r for r in results if r['status'] == 'TRUE']
    
    report_content = ""
    
    if errors:
        report_content += "<h2>🚨 Issues Found (Action Required)</h2>"
        sorted_results = errors + successes
    else:
        report_content += "<h2>✅ Data Integrity Check Status: ALL GOOD</h2>"
        sorted_results = successes

    for entry in sorted_results:
        status_class = f"status-{entry['status']}"
        label_class = f"label-{entry['status']}"
        
        details_html = ""
        details = entry['details']
        
        if entry.get('multi_row', False) and isinstance(details, pd.DataFrame):
            status_col = entry.get('status_check_column')
            headers_html = "".join(f"<th>{h}</th>" for h in details.columns)
            rows_html = ""
            for _, row in details.iterrows():
                cells_html = ""
                for col in details.columns:
                    v = row[col]
                    if isinstance(v, datetime):
                        v_str = v.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        v_str = str(v)
                    td_class = f"class='status-{v_str.upper()}-cell'" if col == status_col else ""
                    cells_html += f"<td {td_class}>{v_str}</td>"
                rows_html += f"<tr>{cells_html}</tr>"
            html_table = f"<table class='details-table'><thead><tr>{headers_html}</tr></thead><tbody>{rows_html}</tbody></table>"

            details_html = f"""
                <p style="margin-top: 10px; font-weight: bold;">Detalhes da Validação por Registro/Dia:</p>
                {html_table}
            """
            
        elif details:
            details_html += "<table class='details-table'><thead><tr><th>Campo</th><th>Valor</th></tr></thead><tbody>"
            for k, v in details.items():
                if isinstance(v, datetime):
                    v_str = v.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    v_str = str(v)
                
                td_class = f"class='status-{v_str.upper()}-cell'" if k == entry['status_check_column'] else ""

                details_html += f"<tr><td>{k}</td><td {td_class}>{v_str}</td></tr>"
            details_html += "</tbody></table>"
        
        report_content += f"""
        <div class='log-entry {status_class}'>
            <h3>{entry['name']}</h3>
            <span class='status-label {label_class}'>{entry['status']}</span>
            <p><em>{entry['description']}</em></p>
            {details_html}
        </div>
        """

    html = f"""
    <html>
    <head>{CSS_STYLE}</head>
    <body>
        <div class='container'>
            <h1>Database Integrity Master Log - {datetime.now().strftime("%Y-%m-%d %H:%M")}</h1>
            <p>Report generated for MSSQL data validation.</p>
            {report_content}
        </div>
    </body>
    </html>
    """

    return html

def send_email(subject, html_body):
    """Connects to SMTP and sends the compiled HTML email."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = config.SENDER_EMAIL
        msg['To'] = config.RECIPIENT_EMAIL
        
        msg.attach(MIMEText(html_body, 'html'))
        
        logging.info("Connecting to SMTP server...")
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            use_tls = getattr(config, 'SMTP_USE_TLS', True)
            if use_tls:
                try:
                    server.starttls()
                except Exception as e:
                    logging.warning(f"STARTTLS não disponível ou falhou: {e}")

            smtp_password = getattr(config, 'SMTP_PASSWORD', None)
            if smtp_password:
                try:
                    server.login(config.SMTP_USERNAME, smtp_password)
                except Exception as e:
                    logging.error(f"Falha na autenticação SMTP: {e}")

            server.sendmail(config.SENDER_EMAIL, config.RECIPIENT_EMAIL, msg.as_string())
        
        logging.info("Email sent successfully!")

    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def main():
    """Main function to run all validations and send the report."""
    logging.info("Starting Data Integrity Validation Process.")
    
    # 1. Initialize SQLAlchemy Engine
    try:
        engine = create_engine(config.DATABASE_URL)
        with engine.connect() as connection:
            logging.info("Successfully connected to the database.")
            
    except Exception as e:
        logging.error(f"Failed to create SQLAlchemy engine or connect: {e}")
        error_html = f"<h1>FATAL ERROR: Database Connection Failed</h1><p>Error: {e}</p>"
        send_email("FATAL: Database Integrity Check Failed", error_html)
        return

    # 2. Run all validations
    validation_results = []
    for validation in DATABASE_VALIDATIONS:
        result = run_validation(engine, validation)
        validation_results.append(result)

    # 3. Create HTML Report
    html_report = create_report_html(validation_results)

    # 4. Determine Email Subject based on results
    has_errors = any(r['status'] in ('FALSE', 'ERROR') for r in validation_results)
    has_warning = any(r['status'] == 'WARNING' for r in validation_results)
    
    if has_errors: # Prioriza o status FALSE/ERROR
        subject = f"🚨 DATA INTEGRITY ALERT: Falhas encontradas em {datetime.now().strftime('%Y-%m-%d')}"
    elif has_warning:
        subject = f"⚠️ DATA INTEGRITY WARNING: Inconsistências Parciais em {datetime.now().strftime('%Y-%m-%d')}"
    else:
        subject = f"✅ Data Integrity Check SUCCESS em {datetime.now().strftime('%Y-%m-%d')}"

    # 5. Send Email
    send_email(subject, html_report)
    
    logging.info("Validation Process Completed.")

if __name__ == "__main__":
    main()