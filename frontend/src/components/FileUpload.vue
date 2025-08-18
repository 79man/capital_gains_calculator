<template>

    <div :class="['upload-item', required ? 'required' : 'optional']">
        <label :for="inputId" class="upload-label">
            <span class="label-text">{{ label }}
                <span v-if="required" class="required-asterisk">*</span></span>
            <input :id="inputId" type="file" :accept="accept" @change="handleFileChange" class="file-input" />
            <div v-if="selectedFile" class="file-status">
                ✓ {{ selectedFile.name }}
            </div>
        </label>
    </div>

</template>

<script>
export default {
    name: 'FileUpload',
    props: {
        label: String,
        accept: String,
        required: Boolean
    },
    emits: ['file-selected'],
    data() {
        return {
            selectedFile: null,
            inputId: `file-input-${Math.random().toString(36).substr(2, 9)}`
        }
    },
    methods: {
        handleFileChange(event) {
            const file = event.target.files[0]
            this.selectedFile = file
            this.$emit('file-selected', file)
        }
    }
}  
</script>
<style scoped>
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
</style>