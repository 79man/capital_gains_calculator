<template>
  <div class="configuration-panel">
    <h3>Configuration Options</h3>

    <div class="config-grid">
      <div class="config-item">
        <label class="checkbox-label">
          <input type="checkbox" :checked="verbose" @change="$emit('update:verbose', $event.target.checked)" />
          <span class="checkmark"></span>
          Verbose Output
        </label>
        <p class="config-description">
          Increase output verbosity for detailed processing information
        </p>
      </div>

      <div class="config-item">
        <label class="checkbox-label">
          <input type="checkbox" :checked="sameSourceOnly"
            @change="$emit('update:same-source-only', $event.target.checked)" />
          <span class="checkmark"></span>
          Same Source Only Mapping
        </label>
        <p class="config-description">
          Allow matching SELL Transactions only with BUY Transactions from same Source/Demat
        </p>
      </div>

      <div class="config-item">
        <label class="checkbox-label">
          <input type="checkbox" :checked="simpleFifoMode"
            @change="$emit('update:simple-fifo-mode', $event.target.checked)" />
          <span class="checkmark"></span>
          Simple FIFO Mode
        </label>
        <p class="config-description">
          Use simple First-In-First-Out lot matching (default: enabled)
        </p>
      </div>
      <div class="config-item">
        <label class="checkbox-label">
          <input type="checkbox" :checked="includeDividends"
            @change="$emit('update:include-dividends', $event.target.checked)" />
          <span class="checkmark"></span>
          Include Dividends
        </label>
        <p class="config-description">
          Include Dividends in Output (default: disabled)
        </p>
      </div>
      <div class="config-item">
        <label>
          <input type="number" 
          :value="ltcgThresholdDays" 
          @input="$emit('update:ltcg-threshold-days', Number($event.target.value)) " />
          LTCG Threshold (in days)
        </label>
        <p class="config-description">
          LTCG Threshold in Days (default: 365)
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ConfigurationPanel',
  props: {
    verbose: {
      type: Boolean,
      default: false
    },
    sameSourceOnly: {
      type: Boolean,
      default: true
    },
    simpleFifoMode: {
      type: Boolean,
      default: true
    },
    includeDividends: {
      type: Boolean,
      default: true
    },
    ltcgThresholdDays: {
      type: Number,
      default: 100
    }
  },
  emits: [
    'update:verbose',
    'update:same-source-only',
    'update:simple-fifo-mode',
    'update:include-dividends',
    'update:ltcg-threshold-days'
  ]
}  
</script>

<style scoped>
.configuration-panel {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  margin: 1rem 0;
}

.configuration-panel h3 {
  margin: 0 0 1rem 0;
  color: #495057;
}

.config-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.config-item {
  background: white;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.checkbox-label input[type="checkbox"] {
  margin-right: 0.5rem;
  transform: scale(1.2);
}

.config-description {
  margin: 0;
  font-size: 0.875rem;
  color: #6c757d;
  line-height: 1.4;
}
</style>