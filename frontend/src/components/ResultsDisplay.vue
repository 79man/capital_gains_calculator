<template>
    <div class="results-display">
        <div class="results-summary">
            <div class="summary-card">
                <h4>Total Transactions</h4>
                <p class="summary-value">{{ totalTransactions }}</p>
            </div>
            <div class="summary-card">
                <h4>LTCG {{ totalLTCGProfit >= 0 ? 'Profit' : 'Loss' }}</h4>
                <!-- <p class="summary-value" :class="totalProfitClass">
                    ₹{{ formatNumber(totalProfit) }}
                </p> -->
                <p class="summary-value" :class="totalLTCGProfitClass">
                    ₹{{ formatNumber(totalLTCGProfit) }}
                </p>
            </div>
            <div class="summary-card">
                <h4>STCG {{ totalSTCGProfit >= 0 ? 'Profit' : 'Loss' }}</h4>
                <p class="summary-value" :class="totalSTCGProfitClass">
                    ₹{{ formatNumber(totalSTCGProfit) }}
                </p>
            </div>
            <div class="summary-card">
                <h4>LTCG Transactions</h4>
                <p class="summary-value">{{ ltcgCount }}</p>
            </div>
            <div class="summary-card">
                <h4>STCG Transactions</h4>
                <p class="summary-value">{{ stcgCount }}</p>
            </div>
        </div>

        <!-- FY Filter -->
        <div class="fy-filter-section">
            <label for="fy-select" class="filter-label">Select Financial Years:</label>
            <div class="multi-select-container">
                <div class="selected-fys" v-if="selectedFYs.length > 0">
                    <span v-for="fy in selectedFYs" :key="fy" :class="['fy-tag', { 'all-years': fy === 'All Years' }]">
                        {{ fy }}
                        <button @click="removeFY(fy)" class="remove-fy">×</button>
                    </span>
                </div>
                <select v-model="selectedFYToAdd" @change="addFY" class="fy-select">
                    <option value="">Add Financial Year...</option>
                    <option v-for="fy in availableFYs" :key="fy" :value="fy">{{ fy }}</option>
                </select>
                <button @click="clearAllFYs" class="clear-all-btn" v-if="selectedFYs.length > 0">
                    Clear All
                </button>
            </div>
        </div>
        <div class="results-header">
            <div class="view-toggle">
                <button @click="currentView = 'detailed'" :class="{ active: currentView === 'detailed' }"
                    class="view-btn">
                    Transactions
                </button>
                <button @click="currentView = 'aggregated'" :class="{ active: currentView === 'aggregated' }"
                    class="view-btn">
                    Summary
                </button>
                <button v-if="dividends" @click="currentView = 'dividends'"
                    :class="{ active: currentView === 'dividends' }" class="view-btn">
                    Dividends
                </button>
            </div>
            <div class="totals-table-actions">
                <h3 class="totals-header">
                    Data
                    <span v-if="selectedFYs.includes('All Years')">
                        (All Years)
                    </span>
                    <span v-else-if="selectedFYs.length > 1">
                        for {{ selectedFYs.length }} selected Years
                    </span>
                    <span v-else-if="selectedFYs.length === 1">
                        for {{ selectedFYs[0] }}
                    </span>
                </h3>
                <button :title="`Quarterly Breakdown ${showQuartersBreakdown ? 'ON' : 'OFF'}`"
                    @click="showQuartersBreakdown = !showQuartersBreakdown" class="toggle-view-btn-switch"
                    :class="{ 'active': showQuartersBreakdown }">

                    <span class="toggle-text">Q {{ showQuartersBreakdown ? '━' : '☰' }}</span>
                </button>
                <!-- <button :title="`Source Breakdown ${showSourceBreakdown ? 'ON' : 'OFF'}`"
                    @click="showSourceBreakdown = !showSourceBreakdown" class="toggle-view-btn-switch"
                    :class="{ 'active': showSourceBreakdown }">

                    <span class="toggle-text">{{ showSourceBreakdown ? '📖' : '📘' }}</span>
                </button> -->
                <button title="Copy Table to Clipboard" @click="copyTableToClipboard()"
                    class="toggle-view-btn-switch deep-hover">

                    <span class="toggle-text">📋</span>
                </button>
            </div>
            <!-- <button @click="downloadResults" class="download-btn">
                <span>📄</span>
                Download CSV
            </button> -->
        </div>

        <!-- Detailed View (existing table) -->
        <div v-if="currentView === 'detailed'" class="detailed-view">
            <!-- pagination for detailed view -->
            <div v-if="totalPages > 1" class="pagination">
                <span class="pagination-info">{{ totalTransactions }} Transactions </span>
                <button @click="currentPage--" :disabled="currentPage === 1" class="pagination-btn">
                    Previous
                </button>
                <span class="pagination-info">
                    Page {{ currentPage }} of {{ totalPages }}
                </span>
                <button @click="currentPage++" :disabled="currentPage === totalPages" class="pagination-btn">
                    Next
                </button>
            </div>
            <div class="results-table-container">
                <table class="results-table" id="transactions-table">
                    <thead>
                        <tr>
                            <th>Sell Source</th>
                            <th>Company Name</th>
                            <th>Transaction Type</th>
                            <th>Sell Date</th>
                            <th>Sell Quantity</th>
                            <th class="right-demarcation">Sell Price</th>
                            <th>Buy Transaction Type</th>
                            <th>Buy Source</th>
                            <th>Buy Date</th>
                            <th>Buy Quantity</th>
                            <th class="right-demarcation">Buy Price</th>
                            <th class="right-demarcation">Adj. Buy Price</th>
                            <th>Sell Value</th>
                            <th>Buy Value</th>
                            <th>Profit</th>
                            <th>Holding Days</th>
                            <th>LTCG/STCG</th>
                            <th>Quarter</th>
                            <th>Financial Year</th>
                            <th>FMV Used?</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(result, index) in paginatedResults" :key="index">
                            <td>{{ result['Sell Source'] }}</td>
                            <td>{{ result['Company Name'] }}</td>
                            <td>{{ result['Transaction Type'] }}</td>
                            <td>{{ result['Sell Date'] }}</td>
                            <td>{{ formatNumber(result['Sell Quantity']) }}</td>
                            <td class="right-demarcation">
                                {{ excelFriendlyFormat ?
                                    formatNumberPlain(result['Sell Price']) : '₹' +
                                    formatNumber(result['Sell Price'])
                                }}
                            </td>
                            <td>{{ result['Buy Transaction Type'] }}</td>
                            <td>{{ result['Buy Source'] }}</td>
                            <td>{{ result['Buy Date'] }}</td>
                            <td>{{ formatNumber(result['Buy Quantity']) }}</td>
                            <td class="right-demarcation">
                                {{ excelFriendlyFormat ?
                                    formatNumberPlain(result['Buy Price']) : '₹' +
                                    formatNumber(result['Buy Price'])
                                }}
                            </td>
                            <td class="right-demarcation">
                                {{ excelFriendlyFormat ?
                                    formatNumberPlain(result['Adj Buy Price']) : '₹' +
                                    formatNumber(result['Adj Buy Price'])
                                }}
                            </td>
                            <td>
                                {{ excelFriendlyFormat ?
                                    formatNumberPlain(result['Sell Value']) : '₹' +
                                    formatNumber(result['Sell Value'])
                                }}
                            </td>
                            <td>
                                {{ excelFriendlyFormat ?
                                    formatNumberPlain(result['Buy Value']) : '₹' +
                                    formatNumber(result['Buy Value'])
                                }}
                            </td>
                            <td :class="getProfitClass(result['Profit'])">
                                {{ excelFriendlyFormat ?
                                    formatNumberPlain(result['Profit']) : '₹' +
                                    formatNumber(result['Profit'])
                                }}
                            </td>
                            <td>
                                {{ result['Holding Days'] }} {{ excelFriendlyFormat ? "" : "days" }}</td>
                            <td>
                                <span :class="getTypeClass(result['LTCG/STCG'])">
                                    {{ result['LTCG/STCG'] }}
                                </span>
                            </td>
                            <td>{{ result['Quarter'] }}</td>
                            <td>{{ result['Financial Year'] }}</td>
                            <td>
                                <span :class="getFMVClass(result['FMV Used?'])">
                                    {{ result['FMV Used?'] }}
                                </span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <!-- pagination for detailed view -->
            <div v-if="totalPages > 1" class="pagination">
                <span class="pagination-info">{{ totalTransactions }} Transactions </span>
                <button @click="currentPage--" :disabled="currentPage === 1" class="pagination-btn">
                    Previous
                </button>
                <span class="pagination-info">
                    Page {{ currentPage }} of {{ totalPages }}
                </span>
                <button @click="currentPage++" :disabled="currentPage === totalPages" class="pagination-btn">
                    Next
                </button>
            </div>
        </div>

        <!-- Hierarchical Aggregated View -->
        <div v-if="currentView === 'aggregated'" class="aggregated-view">
            <!-- Overall Totals Section -->
            <div class="totals-section">

                <div class="fy-totals-table">
                    <table class="totals-table" id="aggregated-totals-table">
                        <thead>
                            <tr>
                                <th></th>
                                <!-- <th v-if="showSourceBreakdown">Source</th> -->
                                <th>Type</th>
                                <th>Transactions</th>
                                <th>Buy Value</th>
                                <th>Sell Value</th>
                                <th>Profit</th>
                            </tr>
                        </thead>

                        <template v-for="(fyData, fy) in aggregatedDataFromSelectedFYs" :key="fy">
                            <tbody class="fy-totals-section">
                                <!-- Quarterly Breakdown (only show when showQuartersBreakdown is true) -->
                                <template v-if="showQuartersBreakdown" v-for="quarter in fyData.availableQuarters"
                                    :key="`${fy}-${quarter}`">
                                    <!-- Quarter LTCG Row -->
                                    <tr class="ltcg-row quarter-row">
                                        <td class="quarter-cell merged-quarter" :rowspan="2">
                                            <div class="quarter-label">{{ quarter }}</div>
                                        </td>
                                        <td class="type-cell quarter-indent">
                                            <span class="type-badge ltcg-badge">LTCG</span>
                                        </td>
                                        <td class="number-cell">{{ fyData.quarters[quarter].ltcg.count }}</td>
                                        <td class="currency-cell">
                                            {{ excelFriendlyFormat ?
                                                formatNumberPlain(fyData.quarters[quarter].ltcg.buyValue) : '₹' +
                                                formatNumber(fyData.quarters[quarter].ltcg.buyValue) }}
                                        </td>
                                        <td class="currency-cell">
                                            {{ excelFriendlyFormat ?
                                                formatNumberPlain(fyData.quarters[quarter].ltcg.sellValue) : '₹' +
                                                formatNumber(fyData.quarters[quarter].ltcg.sellValue) }}
                                        </td>
                                        <td class="currency-cell"
                                            :class="getProfitClass(fyData.quarters[quarter].ltcg.profit)">
                                            {{ excelFriendlyFormat ?
                                                formatNumberPlain(fyData.quarters[quarter].ltcg.profit) : '₹' +
                                                formatNumber(fyData.quarters[quarter].ltcg.profit) }}
                                        </td>
                                    </tr>

                                    <!-- Quarter STCG Row -->
                                    <tr class="stcg-row quarter-row">
                                        <td class="type-cell quarter-indent">
                                            <span class="type-badge stcg-badge">STCG</span>
                                        </td>
                                        <td class="number-cell">{{ fyData.quarters[quarter].stcg.count }}</td>
                                        <td class="currency-cell">
                                            {{ excelFriendlyFormat ?
                                                formatNumberPlain(fyData.quarters[quarter].stcg.buyValue) : '₹' +
                                                formatNumber(fyData.quarters[quarter].stcg.buyValue) }}
                                        </td>
                                        <td class="currency-cell">
                                            {{ excelFriendlyFormat ?
                                                formatNumberPlain(fyData.quarters[quarter].stcg.sellValue) : '₹' +
                                                formatNumber(fyData.quarters[quarter].stcg.sellValue) }}
                                        </td>
                                        <td class="currency-cell"
                                            :class="getProfitClass(fyData.quarters[quarter].stcg.profit)">
                                            {{ excelFriendlyFormat ?
                                                formatNumberPlain(fyData.quarters[quarter].stcg.profit) : '₹' +
                                                formatNumber(fyData.quarters[quarter].stcg.profit) }}
                                        </td>
                                    </tr>
                                </template>
                                <!-- FY Level Totals -->

                                <tr class="ltcg-row">
                                    <td class="quarter-cell merged-quarter" :rowspan="2">
                                        <div class="quarter-label">{{ fy }} {{ !showQuartersBreakdown ? '' : 'Total'
                                        }}
                                        </div>
                                    </td>
                                    <td class="type-cell">
                                        <span class="type-badge ltcg-badge">LTCG</span>
                                    </td>
                                    <td class="number-cell">{{ fyData.ltcg.count }}</td>
                                    <td class="currency-cell">
                                        {{ excelFriendlyFormat ? formatNumberPlain(fyData.ltcg.buyValue) : '₹' +
                                            formatNumber(fyData.ltcg.buyValue) }}
                                    </td>
                                    <td class="currency-cell">
                                        {{ excelFriendlyFormat ? formatNumberPlain(fyData.ltcg.sellValue) : '₹' +
                                            formatNumber(fyData.ltcg.sellValue) }}
                                    </td>
                                    <td class="currency-cell" :class="getProfitClass(fyData.ltcg.profit)">
                                        {{ excelFriendlyFormat ? formatNumberPlain(fyData.ltcg.profit) : '₹' +
                                            formatNumber(fyData.ltcg.profit) }}
                                    </td>
                                </tr>

                                <tr class="stcg-row gray-bottom-border">
                                    <td class="type-cell">
                                        <span class="type-badge stcg-badge">STCG</span>
                                    </td>
                                    <td class="number-cell">{{ fyData.stcg.count }}</td>
                                    <td class="currency-cell">
                                        {{ excelFriendlyFormat ? formatNumberPlain(fyData.stcg.buyValue) : '₹' +
                                            formatNumber(fyData.stcg.buyValue) }}
                                    </td>
                                    <td class="currency-cell">
                                        {{ excelFriendlyFormat ? formatNumberPlain(fyData.stcg.sellValue) : '₹' +
                                            formatNumber(fyData.stcg.sellValue) }}
                                    </td>
                                    <td class="currency-cell" :class="getProfitClass(fyData.stcg.profit)">
                                        {{ excelFriendlyFormat ? formatNumberPlain(fyData.stcg.profit) : '₹' +
                                            formatNumber(fyData.stcg.profit) }}
                                    </td>
                                </tr>
                            </tbody>
                        </template>
                    </table>
                </div>
            </div>
        </div>

        <!-- Dividends View -->
        <div v-if="currentView === 'dividends'" class="detailed-view">
            <div class="results-table-container">
                <table class="results-table" id="dividends-table">
                    <thead>
                        <tr>
                            <th>Company Name</th>
                            <th>Date</th>
                            <th>Amount</th>
                            <th>Quarter</th>
                            <th>Financial Year</th>
                            <th>Source</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(dividend, index) in paginatedDividends" :key="index">
                            <td>{{ dividend['Company Name'] }}</td>
                            <td>{{ dividend['Date'] }}</td>
                            <td class="currency-cell">
                                {{ excelFriendlyFormat ?
                                    formatNumberPlain(dividend['Amount']) : '₹' +
                                    formatNumber(dividend['Amount']) }}
                            </td>
                            <td>{{ dividend['Quarter'] }}</td>
                            <td>{{ dividend['Financial Year'] }}</td>
                            <td>{{ dividend['Source'] }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <!-- pagination for dividends view -->
            <div v-if="totalDividendPages > 1" class="pagination">
                <span class="pagination-info">{{ totalDividendTransactions }} Dividend Transactions </span>
                <button @click="currentDividendPage--" :disabled="currentDividendPage === 1" class="pagination-btn">
                    Previous
                </button>
                <span class="pagination-info">
                    Page {{ currentDividendPage }} of {{ totalDividendPages }}
                </span>
                <button @click="currentDividendPage++" :disabled="currentDividendPage === totalDividendPages"
                    class="pagination-btn">
                    Next
                </button>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'ResultsDisplay',
    props: {
        results: {
            type: Array,
            required: true,
            default: () => []
        },
        dividends: {  // Add this new prop  
            type: Array,
            required: false,
            default: () => []
        }
    },
    emits: ['download'],
    data() {
        return {
            currentPage: 1,
            itemsPerPage: 20,
            currentView: 'aggregated', // 'detailed' or 'aggregated'
            selectedFYs: ['All Years'], // Array of selected FYs instead of single string  
            selectedFYToAdd: '', // Temporary selection for adding FYs
            excelFriendlyFormat: false,
            showQuartersBreakdown: false,
            showSourceBreakdown: false,
            showAllTransactions: false,
            currentDividendPage: 1,
        }
    },
    computed: {

        totalProfitClass() {
            return this.totalProfit >= 0 ? 'profit-positive' : 'profit-negative'
        },

        totalLTCGProfitClass() {
            return this.totalLTCGProfit >= 0 ? 'profit-positive' : 'profit-negative'
        },

        totalSTCGProfitClass() {
            return this.totalSTCGProfit >= 0 ? 'profit-positive' : 'profit-negative'
        },

        // Aggregated View Related calculations
        sortedFYs() {
            if (!Array.isArray(this.results)) return []
            const fys = [...new Set(this.results.map(r => r['Financial Year']))]
            return fys.sort()
        },

        filteredFYs() {
            if (!this.selectedFY) {
                return this.sortedFYs // Show all FYs if none selected  
            }
            return [this.selectedFY] // Show only selected FY  
        },

        availableFYs() {
            if (!Array.isArray(this.results)) return []

            const allFYs = [...new Set(this.results.map(r => r['Financial Year']))].sort()
            const options = ['All Years', ...allFYs]
            // Filter out already selected FYs  
            // Filter out already selected FYs  
            return options.filter(fy => !this.selectedFYs.includes(fy))
        },

        effectiveSelectedFYs() {
            if (!Array.isArray(this.results)) return []

            // If "All Years" is selected, return all available FYs  
            if (this.selectedFYs.includes('All Years')) {
                return [...new Set(this.results.map(r => r['Financial Year']))].sort()
            }

            return this.selectedFYs
        },

        filteredResults() {
            if (!Array.isArray(this.results)) return []

            // Use effectiveSelectedFYs instead of selectedFYs  
            if (this.effectiveSelectedFYs.length === 0) {
                return this.results
            }

            return this.results.filter(result =>
                this.effectiveSelectedFYs.includes(result['Financial Year'])
            )
        },

        filteredDividends() {
            if (!Array.isArray(this.dividends)) return []

            // Use effectiveSelectedFYs instead of selectedFYs  
            if (this.effectiveSelectedFYs.length === 0) {
                return this.dividends
            }

            return this.dividends.filter(dividend =>
                this.effectiveSelectedFYs.includes(dividend['Financial Year'])
            )
        },

        sortedDividendFYs() {
            if (!Array.isArray(this.dividends)) return []
            const fys = [...new Set(this.dividends.map(d => d['Financial Year']))]
            return fys.sort()
        },

        totalDividendAmount() {
            return Object.values(this.dividendDataFromSelectedFYs).reduce((total, fyData) =>
                total + fyData.total.totalAmount, 0
            )
        },

        totalDividendTransactions() {
            return Object.values(this.dividendDataFromSelectedFYs).reduce((total, fyData) =>
                total + fyData.total.count, 0
            )
        },

        dividendDataFromSelectedFYs() {
            if (!Array.isArray(this.dividends)) return {}

            const fyList = this.effectiveSelectedFYs.length > 0 ?
                this.effectiveSelectedFYs :
                this.sortedDividendFYs
            const aggregatedDividends = {}

            fyList.forEach(fy => {
                const fyDividends = this.dividends.filter(dividend => dividend['Financial Year'] === fy)

                const quarters = [...new Set(fyDividends.map(d => d['Quarter']))].sort((a, b) => {
                    const order = { 'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4 }
                    return order[a] - order[b]
                })

                const quarterlyData = {}
                quarters.forEach(quarter => {
                    const quarterDividends = fyDividends.filter(d => d['Quarter'] === quarter)
                    quarterlyData[quarter] = {
                        count: quarterDividends.length,
                        totalAmount: quarterDividends.reduce((sum, d) => sum + (parseFloat(d['Amount']) || 0), 0),
                        transactions: quarterDividends
                    }
                })

                aggregatedDividends[fy] = {
                    total: {
                        count: fyDividends.length,
                        totalAmount: fyDividends.reduce((sum, d) => sum + (parseFloat(d['Amount']) || 0), 0)
                    },
                    quarters: quarterlyData,
                    availableQuarters: quarters,
                    allTransactions: fyDividends
                }
            })

            return aggregatedDividends
        },

        paginatedDividends() {
            if (this.showAllTransactions) {
                return this.detailedDividendsFromAggregated
            }
            const start = (this.currentDividendPage - 1) * this.itemsPerPage
            const end = start + this.itemsPerPage
            return this.detailedDividendsFromAggregated.slice(start, end)
        },

        detailedDividendsFromAggregated() {
            const allDividends = []
            Object.values(this.dividendDataFromSelectedFYs).forEach(fyData => {
                allDividends.push(...fyData.allTransactions)
            })
            return allDividends
        },

        totalDividendPages() {
            return Math.ceil(this.detailedDividendsFromAggregated.length / this.itemsPerPage)
        },

        aggregatedDataFromSelectedFYs() {
            if (!Array.isArray(this.results)) return {}

            // Use effectiveSelectedFYs to handle "All Years" selection  
            const fyList = this.effectiveSelectedFYs.length > 0 ? this.effectiveSelectedFYs : this.sortedFYs

            const aggregatedData = {}

            fyList.forEach(fy => {
                const fyTransactions = this.results.filter(result => result['Financial Year'] === fy)

                // Get all quarters for this FY  
                const quarters = [...new Set(fyTransactions.map(t => t['Quarter']))].sort((a, b) => {
                    const order = { 'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4 }
                    return order[a] - order[b]
                })

                // Calculate FY totals  
                const ltcgTransactions = fyTransactions.filter(t => t['LTCG/STCG'] === 'LTCG')
                const stcgTransactions = fyTransactions.filter(t => t['LTCG/STCG'] === 'STCG')

                // Calculate quarterly data with raw transactions  
                const quarterlyData = {}
                const availableQuartesinFY = [...new Set(fyTransactions.map(t => t['Sell Source']))]
                quarters.forEach(quarter => {
                    const quarterTransactions = fyTransactions.filter(t => t['Quarter'] === quarter)
                    const quarterLTCG = quarterTransactions.filter(t => t['LTCG/STCG'] === 'LTCG')
                    const quarterSTCG = quarterTransactions.filter(t => t['LTCG/STCG'] === 'STCG')

                    const quarterSources = [...new Set(quarterTransactions.map(t => t['Sell Source']))]

                    const quarterlySourceData = {}
                    quarterSources.forEach(source => {
                        const sourceTransactions = quarterTransactions.filter(t => t['Sell Source'] === source)
                        const sourceLTCG = sourceTransactions.filter(t => t['LTCG/STCG'] === 'LTCG')
                        const sourceSTCG = sourceTransactions.filter(t => t['LTCG/STCG'] === 'STCG')
                        quarterlySourceData[source] = {
                            ltcg: {
                                count: sourceLTCG.length,
                                buyValue: sourceLTCG.reduce((sum, t) => sum + (parseFloat(t['Buy Value']) || 0), 0),
                                sellValue: sourceLTCG.reduce((sum, t) => sum + (parseFloat(t['Sell Value']) || 0), 0),
                                profit: sourceLTCG.reduce((sum, t) => sum + (parseFloat(t['Profit']) || 0), 0),
                                transactions: sourceLTCG // Raw transaction rows  
                            },
                            stcg: {
                                count: sourceSTCG.length,
                                buyValue: sourceSTCG.reduce((sum, t) => sum + (parseFloat(t['Buy Value']) || 0), 0),
                                sellValue: sourceSTCG.reduce((sum, t) => sum + (parseFloat(t['Sell Value']) || 0), 0),
                                profit: sourceSTCG.reduce((sum, t) => sum + (parseFloat(t['Profit']) || 0), 0),
                                transactions: sourceSTCG // Raw transaction rows  
                            }
                        }
                    })

                    quarterlyData[quarter] = {
                        ltcg: {
                            count: quarterLTCG.length,
                            buyValue: quarterLTCG.reduce((sum, t) => sum + (parseFloat(t['Buy Value']) || 0), 0),
                            sellValue: quarterLTCG.reduce((sum, t) => sum + (parseFloat(t['Sell Value']) || 0), 0),
                            profit: quarterLTCG.reduce((sum, t) => sum + (parseFloat(t['Profit']) || 0), 0),
                            transactions: quarterLTCG // Raw transaction rows  
                        },
                        stcg: {
                            count: quarterSTCG.length,
                            buyValue: quarterSTCG.reduce((sum, t) => sum + (parseFloat(t['Buy Value']) || 0), 0),
                            sellValue: quarterSTCG.reduce((sum, t) => sum + (parseFloat(t['Sell Value']) || 0), 0),
                            profit: quarterSTCG.reduce((sum, t) => sum + (parseFloat(t['Profit']) || 0), 0),
                            transactions: quarterSTCG // Raw transaction rows  
                        },
                        total: {
                            count: quarterTransactions.length,
                            buyValue: quarterTransactions.reduce((sum, t) => sum + (parseFloat(t['Buy Value']) || 0), 0),
                            sellValue: quarterTransactions.reduce((sum, t) => sum + (parseFloat(t['Sell Value']) || 0), 0),
                            profit: quarterTransactions.reduce((sum, t) => sum + (parseFloat(t['Profit']) || 0), 0),
                            transactions: quarterTransactions // Raw transaction rows  
                        },
                        sources: quarterlySourceData,
                        availableSources: quarterSources,
                    }
                })

                aggregatedData[fy] = {
                    // FY totals with raw transactions  
                    ltcg: {
                        count: ltcgTransactions.length,
                        buyValue: ltcgTransactions.reduce((sum, t) => sum + (parseFloat(t['Buy Value']) || 0), 0),
                        sellValue: ltcgTransactions.reduce((sum, t) => sum + (parseFloat(t['Sell Value']) || 0), 0),
                        profit: ltcgTransactions.reduce((sum, t) => sum + (parseFloat(t['Profit']) || 0), 0),
                        transactions: ltcgTransactions // Raw transaction rows  
                    },
                    stcg: {
                        count: stcgTransactions.length,
                        buyValue: stcgTransactions.reduce((sum, t) => sum + (parseFloat(t['Buy Value']) || 0), 0),
                        sellValue: stcgTransactions.reduce((sum, t) => sum + (parseFloat(t['Sell Value']) || 0), 0),
                        profit: stcgTransactions.reduce((sum, t) => sum + (parseFloat(t['Profit']) || 0), 0),
                        transactions: stcgTransactions // Raw transaction rows  
                    },
                    // Quarterly data  
                    quarters: quarterlyData,
                    availableQuarters: quarters,
                    availableSources: availableQuartesinFY,
                    // All transactions for this FY  
                    allTransactions: fyTransactions
                }
            })

            return aggregatedData
        },

        // Flatten all transactions for detailed view  
        detailedTransactionsFromAggregated() {
            const allTransactions = []
            Object.values(this.aggregatedDataFromSelectedFYs).forEach(fyData => {
                allTransactions.push(...fyData.allTransactions)
            })
            return allTransactions
        },

        // Update existing computed properties  
        totalTransactions() {
            return this.detailedTransactionsFromAggregated.length
        },

        totalProfit() {
            return this.detailedTransactionsFromAggregated.reduce((sum, result) =>
                sum + (parseFloat(result['Profit']) || 0), 0
            )
        },

        totalLTCGProfit() {
            return Object.values(
                this.aggregatedDataFromSelectedFYs
            ).reduce(
                (total, fyData) => total + fyData.ltcg.profit, 0
            )
        },

        totalSTCGProfit() {
            return Object.values(
                this.aggregatedDataFromSelectedFYs
            ).reduce(
                (total, fyData) => total + fyData.stcg.profit, 0
            )
        },


        ltcgCount() {
            return Object.values(this.aggregatedDataFromSelectedFYs).reduce((total, fyData) =>
                total + fyData.ltcg.count, 0
            )
        },

        stcgCount() {
            return Object.values(this.aggregatedDataFromSelectedFYs).reduce((total, fyData) =>
                total + fyData.stcg.count, 0
            )
        },

        paginatedResults() {
            if (this.showAllTransactions) {
                return this.detailedTransactionsFromAggregated;
            }

            const start = (this.currentPage - 1) * this.itemsPerPage
            const end = start + this.itemsPerPage
            return this.detailedTransactionsFromAggregated.slice(start, end)
        },

        totalPages() {
            return Math.ceil(this.detailedTransactionsFromAggregated.length / this.itemsPerPage)
        },


        combinedTotals() {
            const allFYData = Object.values(this.aggregatedDataBySelectedFY)

            return {
                ltcg: {
                    count: allFYData.reduce((sum, fy) => sum + fy.ltcg.count, 0),
                    buyValue: allFYData.reduce((sum, fy) => sum + fy.ltcg.buyValue, 0),
                    sellValue: allFYData.reduce((sum, fy) => sum + fy.ltcg.sellValue, 0),
                    profit: allFYData.reduce((sum, fy) => sum + fy.ltcg.profit, 0)
                },
                stcg: {
                    count: allFYData.reduce((sum, fy) => sum + fy.stcg.count, 0),
                    buyValue: allFYData.reduce((sum, fy) => sum + fy.stcg.buyValue, 0),
                    sellValue: allFYData.reduce((sum, fy) => sum + fy.stcg.sellValue, 0),
                    profit: allFYData.reduce((sum, fy) => sum + fy.stcg.profit, 0)
                }
            }
        }

    },
    methods: {
        addFY() {
            if (this.selectedFYToAdd && !this.selectedFYs.includes(this.selectedFYToAdd)) {
                // If adding "All Years", remove all other selections  
                if (this.selectedFYToAdd === 'All Years') {
                    this.selectedFYs = ['All Years']
                } else {
                    // If adding a specific FY and "All Years" is selected, remove "All Years"  
                    if (this.selectedFYs.includes('All Years')) {
                        this.selectedFYs = this.selectedFYs.filter(fy => fy !== 'All Years')
                    }
                    this.selectedFYs.push(this.selectedFYToAdd)
                    this.selectedFYs.sort()
                }
            }
            this.selectedFYToAdd = ''
        },

        removeFY(fy) {
            const index = this.selectedFYs.indexOf(fy)
            if (index > -1) {
                this.selectedFYs.splice(index, 1)

                // If no FYs are selected after removal, default back to "All Years"  
                if (this.selectedFYs.length === 0) {
                    this.selectedFYs = ['All Years']
                }
            }
        },

        clearAllFYs() {
            this.selectedFYs = ['All Years'] // Reset to default instead of empty array  
        },

        downloadResults() {
            this.$emit('download')
        },
        formatNumber(value) {
            const num = parseFloat(value)
            return isNaN(num) ? value : new Intl.NumberFormat('en-IN', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(num)
        },
        formatNumberPlain(value) {
            const num = parseFloat(value);
            // Check if it's a valid number, otherwise return the original value  
            if (isNaN(num)) {
                return value;
            }
            // Convert to a fixed-point notation string to remove locale-specific formatting  
            // and ensure two decimal places.  
            return num.toFixed(2);
        },
        getProfitClass(profit) {
            const num = parseFloat(profit)
            return num >= 0 ? 'profit-positive' : 'profit-negative'
        },
        getTypeClass(type) {
            return type === 'LTCG' ? 'type-ltcg' : 'type-stcg'
        },

        getFMVClass(fmvUsed) {
            return fmvUsed === 'True' ? 'type-ltcg' : 'type-stcg'
        },

        getLTCGTotals() {
            const ltcgTransactions = this.filteredResults.filter(result =>
                result['LTCG/STCG'] === 'LTCG'
            )

            return {
                count: ltcgTransactions.length,
                buyValue: ltcgTransactions.reduce((sum, t) => sum + (parseFloat(t['Buy Value']) || 0), 0),
                sellValue: ltcgTransactions.reduce((sum, t) => sum + (parseFloat(t['Sell Value']) || 0), 0),
                profit: ltcgTransactions.reduce((sum, t) => sum + (parseFloat(t['Profit']) || 0), 0)
            }
        },

        getSTCGTotals() {
            const stcgTransactions = this.filteredResults.filter(result =>
                result['LTCG/STCG'] === 'STCG'
            )

            return {
                count: stcgTransactions.length,
                buyValue: stcgTransactions.reduce((sum, t) => sum + (parseFloat(t['Buy Value']) || 0), 0),
                sellValue: stcgTransactions.reduce((sum, t) => sum + (parseFloat(t['Sell Value']) || 0), 0),
                profit: stcgTransactions.reduce((sum, t) => sum + (parseFloat(t['Profit']) || 0), 0)
            }
        },

        getTotalTotals() {
            const ltcg = this.getLTCGTotals()
            const stcg = this.getSTCGTotals()

            return {
                count: ltcg.count + stcg.count,
                buyValue: ltcg.buyValue + stcg.buyValue,
                sellValue: ltcg.sellValue + stcg.sellValue,
                profit: ltcg.profit + stcg.profit
            }
        },

        getAvailableQuarters() {
            if (!Array.isArray(this.filteredResults)) return []

            const quarters = [...new Set(this.filteredResults.map(r => r['Quarter']))]
            // Sort quarters in FY order: Q1, Q2, Q3, Q4  
            return quarters.sort((a, b) => {
                const order = { 'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4 }
                return order[a] - order[b]
            })
        },

        getQuarterData(quarter, type) {
            const quarterTransactions = this.filteredResults.filter(result =>
                result['Quarter'] === quarter && result['LTCG/STCG'] === type
            )

            return {
                count: quarterTransactions.length,
                buyValue: quarterTransactions.reduce((sum, t) => sum + (parseFloat(t['Buy Value']) || 0), 0),
                sellValue: quarterTransactions.reduce((sum, t) => sum + (parseFloat(t['Sell Value']) || 0), 0),
                profit: quarterTransactions.reduce((sum, t) => sum + (parseFloat(t['Profit']) || 0), 0)
            }
        },

        getQuarterTotal(quarter) {
            const ltcg = this.getQuarterData(quarter, 'LTCG')
            const stcg = this.getQuarterData(quarter, 'STCG')

            return {
                count: ltcg.count + stcg.count,
                buyValue: ltcg.buyValue + stcg.buyValue,
                sellValue: ltcg.sellValue + stcg.sellValue,
                profit: ltcg.profit + stcg.profit
            }
        },

        old_exportToExcel() {
            const headers = ['Quarter', 'Type', 'Transactions', 'Buy Value', 'Sell Value', 'Profit']
            const rows = []

            // Add header row  
            rows.push(headers.join(','))

            // Add data rows without currency symbols  
            this.getAvailableQuarters().forEach(quarter => {
                // LTCG row  
                const ltcgData = this.getQuarterData(quarter, 'LTCG')
                rows.push([
                    quarter,
                    'LTCG',
                    ltcgData.count,
                    ltcgData.buyValue.toFixed(2),
                    ltcgData.sellValue.toFixed(2),
                    ltcgData.profit.toFixed(2)
                ].join(','))

                // STCG row  
                const stcgData = this.getQuarterData(quarter, 'STCG')
                rows.push([
                    '',
                    'STCG',
                    stcgData.count,
                    stcgData.buyValue.toFixed(2),
                    stcgData.sellValue.toFixed(2),
                    stcgData.profit.toFixed(2)
                ].join(','))

                // Quarter total row  
                const quarterTotal = this.getQuarterTotal(quarter)
                rows.push([
                    '',
                    `${quarter} Total`,
                    quarterTotal.count,
                    quarterTotal.buyValue.toFixed(2),
                    quarterTotal.sellValue.toFixed(2),
                    quarterTotal.profit.toFixed(2)
                ].join(','))
            })

            // Add overall total  
            const total = this.getTotalTotals()
            rows.push([
                'TOTAL',
                'All Quarters',
                total.count,
                total.buyValue.toFixed(2),
                total.sellValue.toFixed(2),
                total.profit.toFixed(2)
            ].join(','))

            // Create and download CSV  
            const csvContent = rows.join('\n')
            const blob = new Blob([csvContent], { type: 'text/csv' })
            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = 'capital_gains_totals.csv'
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            window.URL.revokeObjectURL(url)
        },

        copyTableToClipboard() {
            let oldExcelFormatValue = this.excelFriendlyFormat
            this.excelFriendlyFormat = true;

            let tableName = 'aggregated-totals-table'

            if (this.currentView === 'detailed') {
                // Toggle pagination off to show all transactions  
                this.showAllTransactions = true;

                tableName = 'transactions-table'
            } else if (this.currentView === 'dividends') {
                // Toggle pagination off to show all transactions  
                this.showAllTransactions = true;

                tableName = 'dividends-table'
            }

            // Wait for Vue to update the DOM
            this.$nextTick(() => {
                var table = document.getElementById(tableName);

                // Rest of your clipboard code here...  
                if (navigator.clipboard && window.ClipboardItem) {
                    const html = table.outerHTML;
                    const blob = new Blob([html], { type: "text/html" });
                    const clipboardItem = new ClipboardItem({ "text/html": blob });
                    navigator.clipboard.write([clipboardItem])
                        .then(() => alert('Table copied!\nNow paste it in Excel.'))
                        .catch(err => alert('Copy failed: ' + err));
                } else {
                    // Fallback code...  
                }
                this.showAllTransactions = false;
                this.excelFriendlyFormat = oldExcelFormatValue;
            });
        },

        async old_copyTotalsTableToClipboard() {
            const table = document.createElement('table');
            const thead = table.createTHead();
            const tbody = table.createTBody();

            // Create table headers  
            const headerRow = thead.insertRow();
            ['Quarter', 'Type', 'Transactions', 'Buy Value', 'Sell Value', 'Profit'].forEach(headerText => {
                const th = document.createElement('th');
                th.textContent = headerText;
                headerRow.appendChild(th);
            });

            // Populate table body with data  
            this.getAvailableQuarters().forEach(quarter => {
                // LTCG row  
                const ltcgData = this.getQuarterData(quarter, 'LTCG');
                const ltcgRow = tbody.insertRow();

                // Quarter cell with rowspan  
                const quarterCell = ltcgRow.insertCell();
                quarterCell.rowSpan = 3;
                quarterCell.textContent = quarter;

                ltcgRow.insertCell().textContent = 'LTCG';
                ltcgRow.insertCell().textContent = ltcgData.count;
                ltcgRow.insertCell().textContent = this.formatNumberPlain(ltcgData.buyValue);
                ltcgRow.insertCell().textContent = this.formatNumberPlain(ltcgData.sellValue);
                ltcgRow.insertCell().textContent = this.formatNumberPlain(ltcgData.profit);

                // STCG row  
                const stcgData = this.getQuarterData(quarter, 'STCG');
                const stcgRow = tbody.insertRow();
                stcgRow.insertCell().textContent = 'STCG';
                stcgRow.insertCell().textContent = stcgData.count;
                stcgRow.insertCell().textContent = this.formatNumberPlain(stcgData.buyValue);
                stcgRow.insertCell().textContent = this.formatNumberPlain(stcgData.sellValue);
                stcgRow.insertCell().textContent = this.formatNumberPlain(stcgData.profit);

                // Quarter Total row  
                const quarterTotal = this.getQuarterTotal(quarter);
                const quarterTotalRow = tbody.insertRow();
                quarterTotalRow.insertCell().textContent = `${quarter} Total`;
                quarterTotalRow.insertCell().textContent = quarterTotal.count;
                quarterTotalRow.insertCell().textContent = this.formatNumberPlain(quarterTotal.buyValue);
                quarterTotalRow.insertCell().textContent = this.formatNumberPlain(quarterTotal.sellValue);
                quarterTotalRow.insertCell().textContent = this.formatNumberPlain(quarterTotal.profit);
            });

            // Overall Total row  
            const total = this.getTotalTotals();
            const totalRow = tbody.insertRow();
            totalRow.insertCell().textContent = 'TOTAL';
            totalRow.insertCell().textContent = 'All Quarters';
            totalRow.insertCell().textContent = total.count;
            totalRow.insertCell().textContent = this.formatNumberPlain(total.buyValue);
            totalRow.insertCell().textContent = this.formatNumberPlain(total.sellValue);
            totalRow.insertCell().textContent = this.formatNumberPlain(total.profit);

            try {
                // Use the Clipboard API to write HTML content  
                await navigator.clipboard.write([
                    new ClipboardItem({
                        'text/html': new Blob([table.outerHTML], { type: 'text/html' }),
                        'text/plain': new Blob([table.innerText], { type: 'text/plain' })
                    })
                ]);
                alert('Table copied to clipboard!');
            } catch (err) {
                console.error('Failed to copy table: ', err);
                alert('Failed to copy table to clipboard. Please try again or use the Excel-friendly format and copy manually.');
            }
        },


        getAvailableQuartersForFY(fy) {
            // console.log('getAvailableQuartersForFY(', fy, ')')
            if (!Array.isArray(this.results)) return []

            const fyResults = this.results.filter(
                result => result['Financial Year'] === fy
            )
            const quarters = [...new Set(fyResults.map(r => r['Quarter']))]
            return quarters.sort((a, b) => {
                const order = { 'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4 }
                return order[a] - order[b]
            })
        },

        getQuarterDataForFY(fy, quarter, type) {
            const quarterTransactions = this.results.filter(result =>
                result['Financial Year'] === fy &&
                result['Quarter'] === quarter &&
                result['LTCG/STCG'] === type
            )

            return {
                count: quarterTransactions.length,
                buyValue: quarterTransactions.reduce((sum, t) => sum + (parseFloat(t['Buy Value']) || 0), 0),
                sellValue: quarterTransactions.reduce((sum, t) => sum + (parseFloat(t['Sell Value']) || 0), 0),
                profit: quarterTransactions.reduce((sum, t) => sum + (parseFloat(t['Profit']) || 0), 0)
            }
        },

        getQuarterTotalForFY(fy, quarter) {
            const ltcg = this.getQuarterDataForFY(fy, quarter, 'LTCG')
            const stcg = this.getQuarterDataForFY(fy, quarter, 'STCG')

            return {
                count: ltcg.count + stcg.count,
                buyValue: ltcg.buyValue + stcg.buyValue,
                sellValue: ltcg.sellValue + stcg.sellValue,
                profit: ltcg.profit + stcg.profit
            }
        },
    }
}

</script>

<style scoped>
.results-display {
    background: #f9f9f9;
    /* border-radius: 8px; */
    padding: 1rem;
    /* margin: 1rem 0; */
    /* box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); */
}

.results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.results-header h3 {
    margin: 0;
    color: #495057;
}

.view-toggle {
    display: flex;
    gap: 0.5rem;
}

.view-btn {
    padding: 0.5rem 1rem;
    border: 1px solid #dee2e6;
    background: white;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1.1rem;
    font-weight: 700;
    text-align: center;
}

.view-btn.active {
    background: #007bff;
    color: white;
    border-color: #007bff;
}

.view-btn:hover:not(.active) {
    background: #f8f9fa;
}

.download-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: #28a745;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
}

.download-btn:hover {
    background: #218838;
}

/* Aggregated View Styles */

.fy-section {
    margin-bottom: 2rem;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    overflow: hidden;
}

.fy-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    margin: 0;
    padding: 1rem;
    font-size: 1.25rem;
    font-weight: 600;
}

.quarter-section {
    border-bottom: 1px solid #dee2e6;
    padding: 1.5rem;
}

.quarter-section:last-child {
    border-bottom: none;
}

.quarter-header {
    margin: 0 0 1rem 0;
    color: #495057;
    font-size: 1.1rem;
    font-weight: 600;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #e9ecef;
}

.aggregated-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
}

@media (max-width: 768px) {
    .aggregated-grid {
        grid-template-columns: 1fr;
    }
}

.aggregated-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 1.5rem;
    border-left: 4px solid;
}

.ltcg-card {
    border-left-color: #28a745;
}

.stcg-card {
    border-left-color: #dc3545;
}

.aggregated-card h5 {
    margin: 0 0 1rem 0;
    color: #495057;
    font-size: 1rem;
    font-weight: 600;
}

.aggregated-stats {
    display: grid;
    gap: 0.75rem;
}

.stat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid #dee2e6;
}

.stat-item:last-child {
    border-bottom: none;
}

.stat-label {
    font-weight: 500;
    color: #6c757d;
    font-size: 0.875rem;
}

.stat-value {
    font-weight: 600;
    color: #495057;
    font-size: 0.875rem;
}

/* Existing table and pagination styles remain the same */
.results-summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}

.summary-card {
    background: #ebebeb;
    padding: 1rem;
    border-radius: 6px;
    text-align: center;
}

.summary-card h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
    color: #6c757d;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.summary-value {
    margin: 0;
    font-size: 1.5rem;
    font-weight: bold;
}

.profit-positive {
    color: #28a745;
}

.profit-negative {
    color: #dc3545;
}

.results-table-container {
    overflow-x: auto;
    margin-bottom: 1rem;
}

.results-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    min-width: 1800px;
}

.results-table th,
.results-table td {
    padding: 0.75rem 0.5rem;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
    white-space: nowrap;
}

.results-table th {
    background: #ece7fd;
    font-weight: 600;
    color: #495057;
    position: sticky;
    top: 0;
    z-index: 10;
}

.results-table tbody tr:hover {
    background: #f5f2ff;
}

.type-ltcg {
    background: #d4edda;
    color: #155724;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
}

.type-stcg {
    background: #f8d7da;
    color: #721c24;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
}

.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
    padding: 0.55rem;
}

.pagination-btn {
    background: #007bff;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
}

.pagination-btn:hover:not(:disabled) {
    background: #0056b3;
}

.pagination-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
    opacity: 0.6;
}

.pagination-info {
    font-size: 0.875rem;
    color: #495057;
    font-weight: 500;
}

.fy-filter-section {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 6px;
    display: flex;
    align-items: center;
    gap: 1rem;
    justify-content: space-between;
}

.filter-label {
    font-weight: 600;
    color: #495057;
    margin: 0;
}

.fy-select {
    padding: 0.5rem;
    border: 1px solid #ced4da;
    border-radius: 4px;
    background: white;
    font-size: 0.875rem;
    font-weight: 700;
    min-width: 200px;
}

.fy-select:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.totals-header {
    /* margin: 0 0 1.5rem 0; */
    color: #495057;
    font-size: 1.25rem;
    font-weight: 700;
    text-align: center;
    /* padding-bottom: 0.5rem; */
    /* border-bottom: 2px solid #007bff; */
}

.totals-table-container {
    overflow-x: auto;
    background: white;
    border-radius: 6px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.totals-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}

.totals-table th {
    background: #495057;
    color: white;
    padding: 1rem;
    text-align: center;
    font-weight: 600;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.totals-table th.fy-th {
    text-align: center;
    background: #e0eaf3;
    color: black;
    font-size: 1.1rem;
    padding: 0.25rem;
}


.totals-table td {
    padding: 1rem;
    border-bottom: 1px solid #dee2e6;
    text-align: center;
}

.ltcg-row {
    background: #f8fff9;
}

.ltcg-row:hover {
    background: #e8f5e8;
}

.stcg-row {
    background: #fff8f8;
}

.stcg-row:hover {
    background: #f5e8e8;
}

.gray-bottom-border {
    border-bottom: 3px solid #adb5bd;
}

.total-row {
    background: #f0f0f0;
    font-weight: 700;
    border-top: 2px solid #495057;
}

.total-row:hover {
    background: #e8e8e8;
}

.type-cell {
    font-weight: 600;
    width: 15%;
}

.number-cell {
    text-align: center;
    font-weight: 600;
    width: 15%;
}

.currency-cell {
    text-align: right;
    font-weight: 600;
    font-family: 'Courier New', monospace;
    width: 23.33%;
}

.type-badge {
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.ltcg-badge {
    background: #bbffcb;
    color: black;
}

.stcg-badge {
    background: #ffd5d9;
    color: black;
}

.profit-positive {
    color: #28a745;
}

.profit-negative {
    color: #dc3545;
}

/* Responsive design */
@media (max-width: 768px) {
    .totals-table {
        font-size: 0.8rem;
    }

    .totals-table th,
    .totals-table td {
        padding: 0.75rem 0.5rem;
    }

    .type-badge {
        padding: 0.25rem 0.5rem;
        font-size: 0.7rem;
    }
}

.merged-quarter {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    /* border-right: 3px solid #2196f3; */
    vertical-align: middle;
    text-align: center;
    position: relative;
}

.quarter-label {
    writing-mode: horizontal-tb;
    font-size: 1.1rem;
    font-weight: 700;
    color: #1565c0;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 0.5rem;
}

/* Enhanced quarter cell styling */
.quarter-cell {
    font-weight: 700;
    color: #495057;
    width: 12%;
    vertical-align: middle;
}

/* Add visual separation between quarter groups */
/* .ltcg-row:first-of-type .merged-quarter {
    border-top: 2px solid #2196f3;
} */

.quarter-total-row {
    background: #e9ecef;
    font-weight: 600;
    border-bottom: 3px solid #adb5bd;
}

.quarter-total-row:hover {
    background: #dee2e6;
}

/* Add spacing after each quarter group */
.quarter-total-row+.ltcg-row .merged-quarter {
    border-top: 2px solid #dee2e6;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .quarter-label {
        font-size: 0.9rem;
        padding: 0.25rem;
    }

    .merged-quarter {
        width: 15%;
    }
}

.totals-table-actions {
    display: flex;
    justify-content: flex-end;
    /* Align to the right */
    align-items: center;
    gap: 1rem;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    padding: 0.5rem;
}


.copy-to-clipboard-btn {
    background: #007bff;
    color: white;
    border: none;
    padding: 0.75rem 1.25rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.2s ease;
}

.copy-to-clipboard-btn:hover {
    background: #0056b3;
}

.multi-select-container {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
}

.selected-fys {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.fy-tag {
    background: #007bff;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.fy-tag.all-years {
    background: #28a745;
}

.remove-fy {
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    font-size: 1rem;
    padding: 0;
    width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.remove-fy:hover {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 50%;
}

.clear-all-btn {
    background: #dc3545;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 700;
}

.per-fy-sections {
    margin-bottom: 2rem;
}

.fy-totals-section {
    margin-bottom: 1.5rem;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    overflow: hidden;
}

.fy-totals-header {
    background: #f8f9fa;
    padding: 1rem;
    margin: 0;
    border-bottom: 1px solid #dee2e6;
    color: #495057;
    font-size: 1.1rem;
}

.combined-totals-section {
    border: 2px solid #007bff;
    border-radius: 8px;
    background: white;
    overflow: hidden;
}

.combined-totals-header {
    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
    color: white;
    padding: 1rem;
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    text-align: center;
}

/* Additional responsive styles for multi-select */
@media (max-width: 1024px) {
    .per-fy-sections {
        margin-bottom: 1rem;
    }

    .fy-totals-section {
        margin-bottom: 1rem;
    }
}

@media (max-width: 768px) {
    .multi-select-container {
        flex-direction: column;
        align-items: stretch;
    }

    .selected-fys {
        margin-bottom: 0.5rem;
    }

    .fy-select {
        margin-bottom: 0.5rem;
    }

    .fy-totals-header {
        font-size: 1rem;
        padding: 0.75rem;
    }

    .combined-totals-header {
        font-size: 1rem;
        padding: 0.75rem;
    }
}

/* Hover effects for better UX */
.fy-totals-section:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transform: translateY(-1px);
    transition: all 0.2s ease;
}

.combined-totals-section:hover {
    box-shadow: 0 4px 12px rgba(0, 123, 255, 0.2);
    transform: translateY(-1px);
    transition: all 0.2s ease;
}

.toggle-view-btn {
    background: #6c757d;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.toggle-view-btn:hover {
    background: #5a6268;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toggle-view-btn:active {
    transform: translateY(0);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.toggle-view-btn:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(108, 117, 125, 0.25);
}

/* Alternative styling for when it's active/toggled */
.toggle-view-btn.active {
    background: #007bff;
}

.toggle-view-btn.active:hover {
    background: #0056b3;
}

/* Responsive design */
@media (max-width: 768px) {
    .toggle-view-btn {
        font-size: 0.8rem;
        padding: 0.4rem 0.8rem;
    }
}

/* Icon support if you want to add icons */
.toggle-view-btn::before {
    content: "📊";
    margin-right: 0.25rem;
}

.toggle-view-btn-prominent {
    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
}

.toggle-view-btn-prominent:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
}

.quarter-header-row {
    background: #e9ecef;
}

.quarter-header {
    font-weight: 600;
    color: #495057;
    text-align: center;
    padding: 0.5rem;
    background: #f8f9fa;
    border: 1px solid #dee2e6;
}

.quarter-row {
    background: #fafafa;
}

.quarter-indent {
    padding-left: 2rem;
}

.quarter-total-row {
    background: #e9ecef;
    font-weight: 600;
    border-bottom: 2px solid #adb5bd;
}

.quarter-total-badge {
    background: #6c757d;
    color: white;
    font-size: 0.75rem;
}

.right-demarcation {
    border-right: 2px solid #bdbdbd;
}

.toggle-view-btn-switch {
    display: flex;
    align-items: center;
    /* gap: 0.5rem; */
    padding: 0.5rem 0.5rem;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    background: #dee2e6;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 600;
    color: #495057;
}

.toggle-view-btn-switch.active {
    /* background: linear-gradient(135deg, #28a745 0%, #20c997 100%); */
    color: white;
    /* border-color: #28a745; */
    background: #2679c4;
}

.toggle-view-btn-switch:hover {
    /* transform: translateY(-2px); */
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.toggle-view-btn-switch.deep-hover:hover {
    color: white;
    /* border-color: #28a745; */
    background: #2679c4;
}


.toggle-icon {
    font-size: 1.2rem;
}

.toggle-status {
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.toggle-status.on {
    background: rgba(255, 255, 255, 0.3);
    color: white;
}

.toggle-status.off {
    background: #dc3545;
    color: white;
}

.toggle-view-btn-switch .toggle-text {
    font-size: 1.5rem;
    padding: 0;
    margin: 0;
}
</style>