from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile
import os
import shutil
from processors.capital_gains import CGProcessor
from processors.dividends import DividendProcessor
from processors.base import TransactionProcessor
import zipfile
from .utils import validate_file_type, sanitize_config_input, cleanup_after_delay
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


@api_bp.route('/calculate', methods=['POST'])
def calculate_capital_gains_and_dividends():
    try:
        # Handle file uploads
        transactions_file = request.files.get('transactions_file')
        fmv_file = request.files.get('fmv_file')
        tax_rates_file = request.files.get('tax_rates_file')

        # Validate file types using magic numbers
        csv_mime_types = {'text/csv', 'application/csv', 'text/plain'}
        json_mime_types = {'application/json', 'text/json'}

        if not transactions_file:
            raise ValueError("Transactions file not provided")

        if not validate_file_type(transactions_file, csv_mime_types):
            raise ValueError("Invalid file type for transactions file")

        if fmv_file and not validate_file_type(fmv_file, csv_mime_types):
            raise ValueError("Invalid file type for FMV file")

        if tax_rates_file and not validate_file_type(tax_rates_file, json_mime_types):
            raise ValueError("Invalid file type for tax rates file")

        # Extract configuration parameters
        verbose_setting = sanitize_config_input(
            request.form.get('verbose', 'false'), 'bool'
        )

        same_source_only_setting = sanitize_config_input(
            request.form.get('sameSourceOnly', 'false'), 'bool'
        )

        simple_fifo_mode_setting = sanitize_config_input(
            request.form.get('simpleFifoMode', 'true'), 'bool'
        )

        include_dividends = sanitize_config_input(
            request.form.get('includeDividends', 'false'), 'bool'
        )

        ltcg_threshold_days = sanitize_config_input(
            value=request.form.get('ltcgThresholdDays', 365),
            param_type='int',
            min_val=1,
            max_val=3650
        )

        print(
            f"Settings: verbose_setting:{verbose_setting}, \nsame_source_only_setting: {same_source_only_setting}, \nsimple_fifo_mode_setting:{simple_fifo_mode_setting} \nltcg_threshold_days:{ltcg_threshold_days}")

        # Copy ZIP outside temp directory
        result_fd, result_path = tempfile.mkstemp(
            suffix='.zip', prefix='capital_gains_')
        os.close(result_fd)

        # Save uploaded files temporarily
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use secure_filename for all uploads
            transactions_filename = secure_filename(transactions_file.filename)

            transactions_path = os.path.join(
                temp_dir, transactions_filename)
            transactions_file.save(transactions_path)

            fmv_path = 'Grandfathered_ISIN_Prices.csv'  # Default
            if fmv_file:
                fmv_filename = secure_filename(fmv_file.filename)
                fmv_path = os.path.join(temp_dir, fmv_filename)
                fmv_file.save(fmv_path)

            tax_rates_file_path = ''  # Default
            if tax_rates_file:
                tax_rates_filename = secure_filename(
                    tax_rates_file.filename)
                tax_rates_file_path = os.path.join(
                    temp_dir, tax_rates_filename)
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
            response = send_file(
                result_path,
                as_attachment=True,
                download_name='capital_gains_results.zip',
                mimetype='application/zip'
            )
            cleanup_after_delay(result_path)
            return response

    except Exception as e:
        print(f"Caught Exception: {e}")
        return jsonify({'error': str(e)}), 400
