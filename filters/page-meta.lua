-- Adds to each page's metadata:
--   reading-time-label  "約12分" / "6 min read"
--   site-root           relative path to the site root ("../../")
--   tag-links           [{name, slug}] for the tag links in the title block

local function is_cjk(cp)
  return (cp >= 0x3040 and cp <= 0x30FF)   -- kana
      or (cp >= 0x3400 and cp <= 0x4DBF)   -- CJK ext. A
      or (cp >= 0x4E00 and cp <= 0x9FFF)   -- CJK unified
      or (cp >= 0xF900 and cp <= 0xFAFF)   -- compatibility ideographs
      or (cp >= 0xFF66 and cp <= 0xFF9F)   -- half-width kana
end

local function count(blocks)
  local cjk, words = 0, 0
  local function add(text)
    local in_word = false
    for _, cp in utf8.codes(text) do
      if is_cjk(cp) then
        cjk = cjk + 1
        in_word = false
      elseif (cp >= 0x30 and cp <= 0x39) or (cp >= 0x41 and cp <= 0x5A) or (cp >= 0x61 and cp <= 0x7A) or cp >= 0xC0 and cp < 0x3000 then
        if not in_word then words = words + 1 end
        in_word = true
      else
        in_word = false
      end
    end
  end
  pandoc.Pandoc(blocks):walk({
    Str = function(el) add(el.text) end,
    Code = function(el) add(el.text) end,
    CodeBlock = function(el) add(el.text) end,
  })
  return cjk, words
end

function Pandoc(doc)
  local offset = "."
  if quarto and quarto.project and quarto.project.offset then
    offset = quarto.project.offset
  end
  doc.meta["site-root"] = pandoc.MetaString(offset .. "/")
  local lang = doc.meta.lang and pandoc.utils.stringify(doc.meta.lang) or "ja"
  doc.meta["locale-root"] = pandoc.MetaString(offset .. (lang:sub(1, 2) == "en" and "/en/" or "/"))

  if doc.meta.categories then
    local links = pandoc.List()
    for _, c in ipairs(doc.meta.categories) do
      local name = pandoc.utils.stringify(c)
      links:insert(pandoc.MetaMap({
        name = pandoc.MetaString(name),
        slug = pandoc.MetaString("tag-" .. name:lower():gsub("%s+", "-")),
      }))
    end
    doc.meta["tag-links"] = pandoc.MetaList(links)
  end

  if doc.meta.date == nil then return doc end
  local cjk, words = count(doc.blocks)
  local label
  if lang:sub(1, 2) == "ja" then
    local minutes = math.max(1, math.ceil(cjk / 500 + words / 200))
    label = "約" .. minutes .. "分"
  else
    local minutes = math.max(1, math.ceil(words / 230 + cjk / 500))
    label = minutes .. " min read"
  end
  doc.meta["reading-time-label"] = pandoc.MetaString(label)
  return doc
end
