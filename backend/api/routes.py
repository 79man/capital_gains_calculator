from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile
import os
import shutil
from processors.capital_gains import CGProcessor
from processors.dividends import DividendProcessor
from processors.base import TransactionProcessor
import zipfile

api_bp = Blueprint('api', __name__)


@api_bp.route('/calculate', methods=['POST'])
def calculate_capital_gains_and_dividends():
    try:
        # Handle file uploads
        transactions_file = request.files.get('transactions_file')
        fmv_file = request.files.get('fmv_file')
        tax_rates_file = request.files.get('tax_rates_file')

        # Extract configuration parameters
        verbose_setting = request.form.get(
            'verbose', 'false').lower() == 'true'
        # overwrite_setting = request.form.get('overwrite', 'false').lower() == 'true'
        same_source_only_setting = request.form.get(
            'sameSourceOnly', 'false').lower() == 'true'
        simple_fifo_mode_setting = request.form.get(
            'simpleFifoMode', 'true').lower() == 'true'

        include_dividends = request.form.get(
            'includeDividends', 'false').lower() == 'true'

        ltcg_threshold_days:int = 365
        ltcg_threshold_days_req = request.form.get('ltcgThresholdDays', 365)
        if ltcg_threshold_days_req:
            try:
                ltcg_threshold_days = int(ltcg_threshold_days)
            except ValueError:
                ltcg_threshold_days = 365

        print(
            f"Settings: verbose_setting:{verbose_setting}, \nsame_source_only_setting: {same_source_only_setting}, \nsimple_fifo_mode_setting:{simple_fifo_mode_setting} \nltcg_threshold_days:{ltcg_threshold_days}")

        # Validate file types
        allowed_file_types = {'csv'}
        if not transactions_file:
            raise ValueError("Transactions file not provided")

        if transactions_file and transactions_file.filename.split('.')[-1] not in allowed_file_types:
            raise ValueError("Invalid file type for transactions file")

        if fmv_file and fmv_file.filename.split('.')[-1] not in {'json'}:
            raise ValueError("Invalid file type for fmv file")

        # Copy ZIP outside temp directory
        result_fd, result_path = tempfile.mkstemp(
            suffix='.zip', prefix='capital_gains_')
        os.close(result_fd)

        try:
            # Save uploaded files temporarily
            with tempfile.TemporaryDirectory() as temp_dir:
                transactions_path = os.path.join(temp_dir, 'transactions.csv')
                transactions_file.save(transactions_path)

                fmv_path = 'Grandfathered_ISIN_Prices.csv'  # Default
                if fmv_file:
                    fmv_path = os.path.join(temp_dir, 'fmv.csv')
                    fmv_file.save(fmv_path)

                tax_rates_file_path = ''  # Default
                if tax_rates_file:
                    tax_rates_file_path = os.path.join(
                        temp_dir, 'tax_rates.json')
                    tax_rates_file.save(tax_rates_file_path)

                cg_output_path = os.path.join(temp_dir, 'capital_gains.csv')
                dividend_output_path = os.path.join(temp_dir, 'dividends.csv')

                TransactionProcessor.check_files(
                    transactions_data_file=transactions_path,
                    output_file=cg_output_path,
                    overwrite=True
                )

                transactions_df = TransactionProcessor.initialize_data(
                    transactions_data_file=transactions_path,
                    fmv_data_file=fmv_path
                )

                # Process using existing CGCalculator
                CGProcessor.process_all_transactions(
                    transactions_df=transactions_df,
                    output_file=cg_output_path,
                    overwrite=True,
                    fmv_data_file=fmv_path,
                    tax_rates_file=tax_rates_file_path,
                    verbose=verbose_setting,
                    same_source_only_matching=same_source_only_setting,
                    simple_fifo_mode=simple_fifo_mode_setting,
                    ltcg_threshold_days=ltcg_threshold_days
                )
                files_to_zip = [('capital_gains.csv', cg_output_path)]

                # Process dividends if requested
                if include_dividends:
                    DividendProcessor.process_all_transactions(
                        transactions_df=transactions_df,
                        output_file=dividend_output_path,
                        overwrite=True
                    )
                    files_to_zip.append(
                        ('dividends.csv', dividend_output_path))

                # Create ZIP file
                zip_path = os.path.join(temp_dir, 'results.zip')
                with zipfile.ZipFile(zip_path, 'w') as zip_file:
                    for filename, filepath in files_to_zip:
                        if os.path.exists(filepath):
                            zip_file.write(filepath, filename)

                shutil.copy2(zip_path, result_path)

                # Return results file
                return send_file(
                    result_path,
                    as_attachment=True,
                    download_name='capital_gains_results.zip',
                    mimetype='application/zip'
                )
        finally:
            # Clean up the result file after sending
            if os.path.exists(result_path):
                try:
                    os.unlink(result_path)
                except:
                    pass  # Ignore cleanup errors

    except Exception as e:
        print(f"Caught Exception: {e}")
        return jsonify({'error': str(e)}), 400
