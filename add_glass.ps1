# Add Glassmorphism to All Pages

$files = @(
    "impact.html",
    "index1.html", 
    "join.html",
    "ngo.html",
    "technolgy.html",
    "vision.html",
    "admin\admin.html"
)

foreach ($file in $files) {
    $path = "e:\SWARABHARAT\FRONTEND\$file"
    if (Test-Path $path) {
        $content = Get-Content $path -Raw
        
        # Check if glassmorphism.css is already added
        if ($content -notmatch "glassmorphism.css") {
            # Add after first <link> or <style> tag
            if ($content -match "</head>") {
                $cssPath = if ($file -like "*admin*") { "../css/glassmorphism.css" } else { "css/glassmorphism.css" }
                $content = $content -replace "</head>", "    <link rel=`"stylesheet`" href=`"$cssPath`">`r`n</head>"
                Set-Content $path $content -NoNewline
                Write-Host "Added glassmorphism to $file"
            }
        } else {
            Write-Host "Glassmorphism already in $file"
        }
    }
}

Write-Host "`nGlassmorphism effect added to all pages!"
