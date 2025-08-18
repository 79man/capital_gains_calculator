<template>
    <div class="progress-indicator">
        <div class="progress-content">
            <div class="spinner"></div>
            <h3>Processing Capital Gains...</h3>
            <p>{{ currentStep }}</p>
            <div class="progress-bar">
                <div class="progress-fill" :style="{ width: progress + '%' }"></div>
            </div>
            <p class="progress-text">{{ formatNumber(progress) }}% Complete</p>
        </div>
    </div>
</template>

<script>
export default {
    name: 'ProgressIndicator',
    data() {
        return {
            progress: 0,
            currentStep: 'Initializing...',
            steps: [
                'Loading transaction data...',
                'Processing FMV mappings...',
                'Sorting transactions by date...',
                'Processing company transactions...',
                'Calculating capital gains...',
                'Generating results...',
                'Finalizing output...'
            ]
        }
    },
    mounted() {
        this.simulateProgress()
    },
    methods: {
        simulateProgress() {
            let stepIndex = 0
            const interval = setInterval(() => {
                this.progress += Math.random() * 15

                if (this.progress >= 100) {
                    this.progress = 100
                    this.currentStep = 'Complete!'
                    clearInterval(interval)
                    return
                }

                // Update step based on progress  
                const newStepIndex = Math.floor((this.progress / 100) * this.steps.length)
                if (newStepIndex < this.steps.length && newStepIndex !== stepIndex) {
                    stepIndex = newStepIndex
                    this.currentStep = this.steps[stepIndex]
                }
            }, 500)
        },
        formatNumber(value) {
            const num = parseFloat(value)
            return isNaN(num) ? value : new Intl.NumberFormat('en-IN', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(num)
        }
    }
}  
</script>

<style scoped>
.progress-indicator {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.progress-content {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    text-align: center;
    min-width: 400px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem auto;
}

@keyframes spin {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(360deg);
    }
}

.progress-content h3 {
    margin: 0 0 0.5rem 0;
    color: #495057;
}

.progress-content p {
    margin: 0 0 1rem 0;
    color: #6c757d;
}

.progress-bar {
    width: 100%;
    height: 8px;
    background: #e9ecef;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 0.5rem;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #007bff, #0056b3);
    transition: width 0.3s ease;
}

.progress-text {
    font-size: 0.875rem;
    font-weight: 500;
    color: #495057;
}
</style>