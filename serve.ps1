# Simple static file server for local preview (ASCII only)
$root = $PSScriptRoot
$log  = Join-Path $root 'serve.log'
try {
  $port = 8765
  $listener = New-Object System.Net.HttpListener
  $listener.Prefixes.Add("http://localhost:$port/")
  $listener.Start()
  "STARTED $root : $port" | Out-File $log -Encoding utf8
} catch {
  "FATAL: $_" | Out-File $log -Encoding utf8
  exit 1
}
$mime = @{
  '.html' = 'text/html; charset=utf-8'
  '.js'   = 'application/javascript; charset=utf-8'
  '.css'  = 'text/css'
  '.json' = 'application/json'
  '.png'  = 'image/png'
}
while ($listener.IsListening) {
  try {
    $ctx = $listener.GetContext()
    $name = [Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath).TrimStart('/')
    if (-not $name) { $name = 'index.html' }
    $file = Join-Path $root ($name -replace '/', '\')
    if ((Test-Path $file -PathType Leaf) -and ((Resolve-Path $file).Path.StartsWith($root))) {
      $bytes = [IO.File]::ReadAllBytes($file)
      $ext = [IO.Path]::GetExtension($file).ToLower()
      $ctx.Response.ContentType = if ($mime.ContainsKey($ext)) { $mime[$ext] } else { 'application/octet-stream' }
      $ctx.Response.ContentLength64 = $bytes.Length
      $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    } else {
      $ctx.Response.StatusCode = 404
      $b = [Text.Encoding]::UTF8.GetBytes('404 Not Found')
      $ctx.Response.OutputStream.Write($b, 0, $b.Length)
    }
    $ctx.Response.Close()
  } catch {
    "ERR: $_" | Out-File $log -Append -Encoding utf8
    break
  }
}
