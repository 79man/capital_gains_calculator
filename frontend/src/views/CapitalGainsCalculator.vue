<template>
    <div class="capital-gains-calculator">

        <!-- Compact Upload Section -->
        <div class="collapsible-section">
            <div class="section-header" @click="toggleConfigSection">
                <h3>Configuration Settings</h3>
                <button class="collapse-btn" :class="{ 'collapsed': !showConfigSection }">
                    {{ showConfigSection ? '−' : '+' }}
                </button>
            </div>
            <div v-show="showConfigSection" class="section-content">
                <div class="upload-grid">
                    <FileUpload label="Transaction Data (Required)" accept=".csv"
                        @file-selected="handleTransactionsFile" required />

                    <FileUpload label="FMV Data (Optional)" accept=".csv" @file-selected="handleFMVFile" />

                    <FileUpload label="Tax Rates JSON (Optional)" accept=".json" @file-selected="handleTaxRatesFile" />
                </div>

                <div class="">
                    <!-- <ConfigurationPanel v-model:verbose="config.verbose" v-model:overwrite="config.overwrite" /> -->
                    <ConfigurationPanel :verbose="config.verbose" :same-source-only="config.sameSourceOnly"
                        :simple-fifo-mode="config.simpleFifoMode" :include-dividends="config.includeDividends"
                        :ltcg-threshold-days="config.ltcgThresholdDays" @update:verbose="config.verbose = $event"
                        @update:same-source-only="config.sameSourceOnly = $event"
                        @update:simple-fifo-mode="config.simpleFifoMode = $event"
                        @update:include-dividends="config.includeDividends = $event"
                        @update:ltcg-threshold-days="config.ltcgThresholdDays = $event" />
                </div>

                <div class="config-grid">
                    <div>
                        <button @click="calcCapitalGains" :disabled="!transactionsFile || processing"
                            class="calculate-btn">
                            {{ processing ? 'Processing...' : 'Calculate Capital Gains' }}
                        </button>
                        <div v-if="processingError != null" class="api-error">{{ processingError }}</div>
                    </div>
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
            </div>
        </div>

        <ProgressIndicator v-if="processing" />
        <ResultsDisplay v-if="results" :results="results" :dividends="dividends" @download="handleDownload" />
    </div>
</template>

<script>
import FileUpload from '@/components/FileUpload.vue'
import ConfigurationPanel from '@/components/ConfigurationPanel.vue'
import ResultsDisplay from '@/components/ResultsDisplay.vue'
import ProgressIndicator from '@/components/ProgressIndicator.vue'
import { calculateCapitalGains } from '@/services/api.js'
import JSZip from 'jszip'

export default {
    name: 'CapitalGainsCalculator',
    components: {
        FileUpload,
        ConfigurationPanel,
        ResultsDisplay,
        ProgressIndicator
    },
    data() {
        return {
            transactionsFile: null,
            fmvFile: null,
            taxRatesFile: null,
            config: {
                verbose: false,
                sameSourceOnly: false,
                simpleFifoMode: true,
                includeDividends: false,
                ltcgThresholdDays: 365,
            },
            processing: false,
            csvBlob: null, // Store the original CSV blob  
            zipBlob: null, // Used for new zip blob approach
            results: null, // CG calculations from backend
            dividends: null, // Dividends results from backend
            showConfigSection: true,
            processingError: null
        }
    },
    methods: {
        handleTransactionsFile(file) {
            this.transactionsFile = file
        },
        handleFMVFile(file) {
            this.fmvFile = file
        },
        handleTaxRatesFile(file) {
            this.taxRatesFile = file
        },
        toggleConfigSection() {
            this.showConfigSection = !this.showConfigSection
        },
        async calcCapitalGains() {
            this.processing = true
            this.processingError = null

            try {
                // Validate required files  
                if (!this.transactionsFile) {
                    throw new Error('Transactions file is required')
                }

                // Validate LTCG threshold  
                if (this.config.ltcgThresholdDays < 1 || this.config.ltcgThresholdDays > 3650) {
                    throw new Error('LTCG threshold must be between 1 and 3650 days')
                }

                const formData = new FormData()
                formData.append('transactions_file', this.transactionsFile)
                if (this.fmvFile) formData.append('fmv_file', this.fmvFile)
                if (this.taxRatesFile) formData.append('tax_rates_file', this.taxRatesFile)

                // Add all config properties  
                Object.keys(this.config).forEach(key => {
                    formData.append(key, this.config[key])
                })

                await this.processTransactions(formData)

                // Auto-collapse sections after successful calculation  
                this.showConfigSection = false
            } catch (error) {
                console.error('Capital Gains Calculation failed:', error)
                this.processingError = error.message || "Error in calling API"
                // Handle error display  
            } finally {
                this.processing = false
            }
        },
        parseCSV(csvText) {
            if (!csvText || typeof csvText !== 'string') {
                throw new Error('Invalid CSV text provided')
            }
            const lines = csvText.split('\n').filter(line => line.trim().length > 0)

            if (lines.length === 0) {
                throw new Error('CSV file is empty')
            }

            // Parse CSV with proper quote handling  
            const parseCSVLine = (line) => {
                const result = []
                let current = ''
                let inQuotes = false

                for (let i = 0; i < line.length; i++) {
                    const char = line[i]
                    const nextChar = line[i + 1]

                    if (char === '"') {
                        if (inQuotes && nextChar === '"') {
                            current += '"'
                            i++ // Skip next quote  
                        } else {
                            inQuotes = !inQuotes
                        }
                    } else if (char === ',' && !inQuotes) {
                        result.push(current.trim())
                        current = ''
                    } else {
                        current += char
                    }
                }
                result.push(current.trim())
                return result
            }
            const headers = parseCSVLine(lines[0])
            const results = []

            for (let i = 1; i < lines.length; i++) {
                const values = parseCSVLine(lines[i])
                // Skip rows that are completely empty  
                if (values.every(val => !val)) {
                    continue
                }
                const row = {}
                headers.forEach((header, index) => {
                    row[header.trim()] = values[index]?.trim()
                })
                results.push(row)
            }

            return results
        },
        // Handle the download event from ResultsDisplay  
        handleDownload() {
            if (this.csvBlob) {
                const url = window.URL.createObjectURL(this.csvBlob)
                const link = document.createElement('a')
                link.href = url
                link.download = 'capital_gains_results.csv'
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                window.URL.revokeObjectURL(url)
            }
        },
        async processTransactions(formData) {
            try {
                this.zipBlob = await calculateCapitalGains(formData);

                // Check if it's a ZIP file  
                const isZipFile = this.zipBlob.type === 'application/zip' ||
                    this.zipBlob.type === 'application/x-zip-compressed';

                if (isZipFile) {
                    // Use JSZip to extract files  
                    const zip = await JSZip.loadAsync(this.zipBlob);

                    // Extract capital gains CSV  
                    const cgFile = zip.file('capital_gains.csv');
                    if (cgFile) {
                        const cgText = await cgFile.async('text');
                        this.results = this.parseCSV(cgText);
                    } else {
                        this.results = null;
                    }

                    // Extract dividends CSV if present  
                    const dividendsFile = zip.file('dividends.csv');
                    if (dividendsFile) {
                        const dividendsText = await dividendsFile.async('text');
                        this.dividends = this.parseCSV(dividendsText);
                    } else {
                        this.dividends = null;
                    }
                } else {
                    // Handle single CSV file  
                    const csvText = await this.csvBlob.text();
                    this.results = this.parseCSV(csvText);
                    this.zipBlob = null;
                    this.dividends = null;
                }
            } catch (error) {
                console.error('Processing error:', error.message);
                throw error;
            }
        }
    }
} 
</script>

<style scoped>
.compact-upload-section {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1rem 0;
    border: 2px dashed #dee2e6;
}

.compact-upload-section h3 {
    margin: 0 0 1rem 0;
    color: #495057;
    font-size: 1.1rem;
}

.upload-grid {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 1rem;
}

@media (max-width: 768px) {
    .upload-grid {
        grid-template-columns: 1fr;
    }
}

.upload-item {
    background: white;
    border-radius: 6px;
    padding: 1rem;
    border: 1px solid #dee2e6;
    transition: all 0.2s ease;
}

.upload-item:hover {
    border-color: #007bff;
    box-shadow: 0 2px 4px rgba(0, 123, 255, 0.1);
}

.upload-item.required {
    border-left: 4px solid #dc3545;
}

.upload-item.optional {
    border-left: 4px solid #6c757d;
}

.upload-label {
    display: block;
    cursor: pointer;
    width: 100%;
}

.label-text {
    display: block;
    font-weight: 600;
    color: #495057;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
}

.required-asterisk {
    color: #dc3545;
}

.file-input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 0.875rem;
    background: #fff;
}

.file-input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.file-status {
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: #28a745;
    font-weight: 500;
    padding: 0.25rem 0.5rem;
    background: #d4edda;
    border-radius: 4px;
    border: 1px solid #c3e6cb;
}

.collapsible-section {
    margin-bottom: 0.5rem;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    overflow: hidden;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: #e7dfff;
    cursor: pointer;
    transition: background-color 0.2s ease;
}

.section-header:hover {
    background: #e9ecef;
}

.section-header h3 {
    margin: 0;
    color: #495057;
}

.collapse-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    font-weight: bold;
    color: #6c757d;
    cursor: pointer;
    transition: transform 0.2s ease;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.collapse-btn.collapsed {
    transform: rotate(0deg);
}

.section-content {
    padding: 1.5rem;
    background: #f3f3f3;
    transition: all 0.5s ease;
}

.api-error {
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: #a72828;
    font-weight: 500;
    padding: 0.25rem 0.5rem;
    background: #edd4d4;
    border-radius: 4px;
    border: 1px solid #e6c3c3;
}
</style>