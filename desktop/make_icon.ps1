# Generate app icons: build/icon.png (512) + build/icon.ico (multi-size, real ICO)
# macOS .icns is NOT generated here -- electron-builder converts the png
# via iconutil on the macOS runner during the build.
#
# IMPORTANT: Bitmap.Save(path, ImageFormat.Icon) does NOT work in .NET/GDI+ --
# it silently writes PNG bytes, and rcedit rejects it with
# "Reserved header is not 0 or image type is not icon".
# So the ICO container (ICONDIR + ICONDIRENTRY + BMP/DIB images) is built by hand.
#
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

# Build one ICO image entry: BITMAPINFOHEADER + XOR (BGRA, bottom-up) + AND mask
function Get-IcoImageBytes([System.Drawing.Bitmap]$bmp) {
    $w = $bmp.Width
    $h = $bmp.Height
    $rect = New-Object System.Drawing.Rectangle 0, 0, $w, $h
    $lock = $bmp.LockBits($rect,
        [System.Drawing.Imaging.ImageLockMode]::ReadOnly,
        [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $stride = [Math]::Abs($lock.Stride)
        $src = New-Object byte[] ($stride * $h)
        [System.Runtime.InteropServices.Marshal]::Copy($lock.Scan0, $src, 0, $src.Length)
    } finally {
        $bmp.UnlockBits($lock)
    }

    $rowBytes = $w * 4
    # XOR bitmap: rows stored bottom-up, pixel order BGRA (matches little-endian ARGB)
    $xor = New-Object byte[] ($rowBytes * $h)
    for ($y = 0; $y -lt $h; $y++) {
        [Array]::Copy($src, ($h - 1 - $y) * $stride, $xor, $y * $rowBytes, $rowBytes)
    }
    # AND mask: 1bpp, each row padded to 4 bytes; all zero = use alpha channel
    $maskStride = [int][Math]::Ceiling($w / 32.0) * 4
    $andMask = New-Object byte[] ($maskStride * $h)

    $ms = New-Object System.IO.MemoryStream
    $bw = New-Object System.IO.BinaryWriter($ms)
    $bw.Write([int]40)                                  # biSize
    $bw.Write([int]$w)                                  # biWidth
    $bw.Write([int]($h * 2))                            # biHeight = XOR + AND
    $bw.Write([uint16]1)                                # biPlanes
    $bw.Write([uint16]32)                               # biBitCount
    $bw.Write([int]0)                                   # biCompression = BI_RGB
    $bw.Write([int]($xor.Length + $andMask.Length))     # biSizeImage
    $bw.Write([int]0)                                   # biXPelsPerMeter
    $bw.Write([int]0)                                   # biYPelsPerMeter
    $bw.Write([int]0)                                   # biClrUsed
    $bw.Write([int]0)                                   # biClrImportant
    $bw.Write($xor)
    $bw.Write($andMask)
    $bw.Flush()
    $bytes = $ms.ToArray()
    $bw.Dispose()
    $ms.Dispose()
    return $bytes
}

$sizes = @(16, 24, 32, 48, 64, 128, 256)

$master = New-IconBitmap 512
$pngPath = Join-Path $dir "icon.png"
$master.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)

$images = New-Object System.Collections.ArrayList
foreach ($s in $sizes) {
    $bmp = New-Object System.Drawing.Bitmap $s, $s
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = 'HighQuality'
    $g.InterpolationMode = 'HighQualityBicubic'
    $g.PixelOffsetMode = 'HighQuality'
    $g.Clear([System.Drawing.Color]::Transparent)
    $g.DrawImage($master, 0, 0, $s, $s)
    $g.Dispose()
    [void]$images.Add((Get-IcoImageBytes $bmp))
    $bmp.Dispose()
}
$master.Dispose()

# --- write ICO container ---
$icoPath = Join-Path $dir "icon.ico"
$fs = New-Object System.IO.FileStream($icoPath, [System.IO.FileMode]::Create)
$bw = New-Object System.IO.BinaryWriter($fs)
$bw.Write([uint16]0)                # reserved, must be 0
$bw.Write([uint16]1)                # type: 1 = icon
$bw.Write([uint16]$sizes.Count)     # image count

$offset = 6 + 16 * $sizes.Count
for ($i = 0; $i -lt $sizes.Count; $i++) {
    $s = [int]$sizes[$i]
    $code = if ($s -eq 256) { 0 } else { $s }   # 256 is encoded as 0
    $len = $images[$i].Length
    $bw.Write([byte]$code)          # width
    $bw.Write([byte]$code)          # height
    $bw.Write([byte]0)              # color count (0 = >256 colors)
    $bw.Write([byte]0)              # reserved, must be 0
    $bw.Write([uint16]1)            # planes
    $bw.Write([uint16]32)           # bits per pixel
    $bw.Write([uint32]$len)         # bytes in resource
    $bw.Write([uint32]$offset)      # offset to image data
    $offset += $len
}
foreach ($img in $images) { $bw.Write([byte[]]$img) }
$bw.Dispose()
$fs.Dispose()

Get-ChildItem $dir | Select-Object Name, @{n='KB';e={[math]::Round($_.Length/1KB,1)}}
