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

# Process sample.mp4 with each template
for template in "${templates[@]}"; do
    echo "Processing with template: $template"
    output_file="sample_${template}.mp4"
    
    # Run pycaps with the template and AI word highlighting
    pycaps render --input sample.mp4 --output "$output_file" --template "$template" --ai-word-highlighting
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully processed with $template template -> $output_file"
    else
        echo "❌ Failed to process with $template template"
    fi
    echo "----------------------------------------"
done

echo "🎉 All templates processed!"
echo "Generated files:"
ls -la sample_*.mp4