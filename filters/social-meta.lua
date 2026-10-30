-- Quarto supplies the social title, description and image, but not og:url/type.
local function escape_attribute(value)
  return value:gsub("&", "&amp;"):gsub('"', "&quot;")
    :gsub("<", "&lt;"):gsub(">", "&gt;")
end

function Meta(meta)
  if not quarto.doc.is_format("html") or not meta["social-site-url"]
    or meta["open-graph"] == false then
    return meta
  end
  local output = quarto.doc.project_output_file()
  if not output then return meta end
  output = output:gsub("\\", "/")
  local kind = (output:match("^posts/") or output:match("^en/posts/")) and "article" or "website"
  -- Match the directory URLs used by the site's article links.
  local path = output == "index.html" and "" or output:gsub("/index%.html$", "/")
  path = path:gsub("([^%w%-%._~/])", function(char)
    return string.format("%%%02X", string.byte(char))
  end)
  local base = pandoc.utils.stringify(meta["social-site-url"]):gsub("/+$", "")
  quarto.doc.include_text("in-header",
    '<meta property="og:url" content="' .. escape_attribute(base .. "/" .. path) .. '">\n'
    .. '<meta property="og:type" content="' .. kind .. '">')
  return meta
end
