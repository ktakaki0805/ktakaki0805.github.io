-- Typesetting of cross-references and caption labels.
--   ja: 図 1 -> 図1, 表 1 -> 表1, 式 1 -> 式 (1), セクション 1 -> 第1節
--   en: Equation 1 -> Equation (1)
-- Caption labels ("図1", "Figure 1") are wrapped in <span class="caption-label">
-- and the ":" delimiter is dropped, so the label can be set in bold.
-- Emphasis that contains Japanese becomes <em class="ja"> (set with sesame dots
-- instead of a fake italic); "命題 1" becomes "命題1" and "証明." becomes "証明".

local NBSP = "\u{a0}"

local function split_label(text)
  local prefix, num = text:match("^(.-)" .. NBSP .. "(.+)$")
  if not prefix then prefix, num = text:match("^(.-) (.+)$") end
  return prefix, num
end

local function format_ref(text, ja)
  local prefix, num = split_label(text)
  if not prefix or prefix == "" then return nil end
  if ja then
    if prefix == "式" then return "式" .. NBSP .. "(" .. num .. ")" end
    if prefix == "セクション" or prefix == "節" then return "第" .. num .. "節" end
    return prefix .. num
  else
    if prefix == "Equation" or prefix == "Eq." then return prefix .. NBSP .. "(" .. num .. ")" end
    return nil
  end
end

local function has_cjk(text)
  for _, cp in utf8.codes(text) do
    if (cp >= 0x3040 and cp <= 0x30FF) or (cp >= 0x3400 and cp <= 0x9FFF) or (cp >= 0xF900 and cp <= 0xFAFF) then
      return true
    end
  end
  return false
end

local function format_caption(inlines, ja)
  -- Find the first Str that ends with ":" (Quarto's title delimiter).
  local stop
  for i, el in ipairs(inlines) do
    if el.t == "Str" and el.text:sub(-1) == ":" then stop = i break end
    if el.t ~= "Str" and el.t ~= "Space" then return nil end
    if i > 6 then return nil end
  end
  if not stop then return nil end
  local label = {}
  for i = 1, stop do
    local el = inlines[i]
    label[#label + 1] = (el.t == "Str") and el.text or " "
  end
  local text = table.concat(label):sub(1, -2)
  if ja then
    text = text:gsub(NBSP, ""):gsub(" ", "")
  end
  local out = pandoc.Inlines({ pandoc.Span(pandoc.Inlines(text), { class = "caption-label" }) })
  local rest = stop + 1
  if inlines[rest] and inlines[rest].t == "Space" then rest = rest + 1 end
  if inlines[rest] then out:insert(pandoc.Space()) end
  for i = rest, #inlines do out:insert(inlines[i]) end
  return out
end

function Pandoc(doc)
  local lang = doc.meta.lang and pandoc.utils.stringify(doc.meta.lang) or "ja"
  local ja = lang:sub(1, 2) == "ja"

  local function fix_blocks(blocks)
    local prev
    for i, b in ipairs(blocks) do
      if prev and prev.t == "RawBlock" and prev.text:match("^<figcaption") and (b.t == "Plain" or b.t == "Para") then
        local new = format_caption(b.content, ja)
        if new then b.content = new end
      end
      prev = b
    end
    return blocks
  end

  doc = doc:walk({
    Emph = function(el)
      if has_cjk(pandoc.utils.stringify(el.content)) then
        local out = pandoc.Inlines({ pandoc.RawInline("html", '<em class="ja">') })
        out:extend(el.content)
        out:insert(pandoc.RawInline("html", "</em>"))
        return out
      end
    end,
    Span = function(el)
      if not ja then return nil end
      if el.classes:includes("theorem-title") then
        return el:walk({ Str = function(s) return pandoc.Str((s.text:gsub(NBSP, ""))) end, Space = function() return {} end })
      end
      if el.classes:includes("proof-title") then
        local label = pandoc.utils.stringify(el.content):gsub("[%.%s]+$", "")
        return pandoc.Span(pandoc.Inlines(label), el.attr)
      end
    end,
    Link = function(el)
      if el.classes:includes("quarto-xref") then
        local new = format_ref(pandoc.utils.stringify(el.content), ja)
        if new then el.content = pandoc.Inlines(new) end
        return el
      end
    end,
    Blocks = fix_blocks,
  })
  return doc
end
