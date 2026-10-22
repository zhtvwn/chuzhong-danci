# Generate app icons: build/icon.png (512) + build/icon.ico (256)
# macOS .icns is NOT generated here -- electron-builder converts the png
# via iconutil on the macOS runner during the build.
# NOTE: keep this file pure ASCII; PowerShell 5.1 reads .ps1 as ANSI
# and would mangle non-ASCII bytes, breaking the parser.
Add-Type -AssemblyName System.Drawing

$dir = Join-Path $PSScriptRoot "build"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

# U+8BCD = CJK char used as the app glyph
$glyph = [char]0x8BCD

function New-IconBitmap([int]$size) {
    $bmp = New-Object System.Drawing.Bitmap $size, $size
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = 'HighQuality'
    $g.InterpolationMode = 'HighQualityBicubic'
    $g.PixelOffsetMode = 'HighQuality'
    $g.Clear([System.Drawing.Color]::Transparent)

    # iOS-blue gradient rounded square
    $r = [int]($size * 0.2237)
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = $r * 2
    $path.AddArc(0, 0, $d, $d, 180, 90)
    $path.AddArc($size - $d, 0, $d, $d, 270, 90)
    $path.AddArc($size - $d, $size - $d, $d, $d, 0, 90)
    $path.AddArc(0, $size - $d, $d, $d, 90, 90)
    $path.CloseFigure()

    $rect = New-Object System.Drawing.Rectangle 0, 0, $size, $size
    $brush = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
        $rect,
        [System.Drawing.Color]::FromArgb(255, 10, 132, 255),
        [System.Drawing.Color]::FromArgb(255, 0, 98, 204),
        [System.Drawing.Drawing2D.LinearGradientMode]::Vertical)
    $g.FillPath($brush, $path)

    # white glyph centered
    $fontSize = [int]($size * 0.52)
    $font = New-Object System.Drawing.Font("Microsoft YaHei", $fontSize, [System.Drawing.FontStyle]::Bold)
    $sf = New-Object System.Drawing.StringFormat
    $sf.Alignment = 'Center'
    $sf.LineAlignment = 'Center'
    $rectf = New-Object System.Drawing.RectangleF 0, ($size * 0.02), $size, $size
    $g.DrawString($glyph, $font, [System.Drawing.Brushes]::White, $rectf, $sf)

    $g.Dispose()
    return $bmp
}

$png = New-IconBitmap 512
$pngPath = Join-Path $dir "icon.png"
$png.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)

$icoBmp = New-Object System.Drawing.Bitmap 256, 256
$ig = [System.Drawing.Graphics]::FromImage($icoBmp)
$ig.InterpolationMode = 'HighQualityBicubic'
$ig.DrawImage($png, 0, 0, 256, 256)
$ig.Dispose()
$icoPath = Join-Path $dir "icon.ico"
$icoBmp.Save($icoPath, [System.Drawing.Imaging.ImageFormat]::Icon)

$png.Dispose()
$icoBmp.Dispose()
Get-ChildItem $dir | Select-Object Name, @{n='KB';e={[math]::Round($_.Length/1KB,1)}}
