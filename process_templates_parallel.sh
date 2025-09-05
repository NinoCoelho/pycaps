#!/bin/bash

# List of all templates
templates=(
    "classic"
    "default"
    "explosive"
    "fast"
    "hype"
    "line-focus"
    "minimalist"
    "model"
    "neo-minimal"
    "redpill"
    "retro-gaming"
    "vibrant"
    "word-focus"
)

# Function to process a single template
process_template() {
    template=$1
    echo "🚀 Starting: $template"
    output_file="sample_${template}.mp4"
    
    # Run pycaps with the template and AI word highlighting
    pycaps render --input sample.mp4 --output "$output_file" --template "$template" --ai-word-highlighting 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Completed: $template -> $output_file"
    else
        echo "❌ Failed: $template"
    fi
}

# Export the function so it's available to parallel
export -f process_template

# Process templates in parallel (max 4 at a time to avoid overwhelming the system)
echo "🎬 Processing sample.mp4 with all templates in parallel..."
echo "This will process 4 templates simultaneously to speed things up."
echo "----------------------------------------"

# Use GNU parallel if available, otherwise fall back to background jobs
if command -v parallel &> /dev/null; then
    echo "Using GNU parallel..."
    parallel -j 4 process_template ::: "${templates[@]}"
else
    echo "Using background jobs (max 4 concurrent)..."
    
    # Process in batches of 4
    for ((i=0; i<${#templates[@]}; i+=4)); do
        # Start up to 4 background jobs
        for ((j=i; j<i+4 && j<${#templates[@]}; j++)); do
            process_template "${templates[$j]}" &
        done
        
        # Wait for this batch to complete
        wait
    done
fi

echo "----------------------------------------"
echo "🎉 All templates processed!"
echo ""
echo "Generated files:"
ls -la sample_*.mp4 2>/dev/null | grep -v "No such file"

# Count successful outputs
count=$(ls sample_*.mp4 2>/dev/null | wc -l)
echo ""
echo "Successfully generated $count out of ${#templates[@]} template videos."