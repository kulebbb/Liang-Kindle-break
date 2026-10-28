--[[--
Bookdrop QR：在 Kindle 上显示局域网传书页面的二维码，手机扫码即可上传电子书。
地址由电脑端 Bookdrop 启动时写入 /mnt/us/koreader/bookdrop_url.txt：
第一行是网页地址，第二行是 SSH 直连信息（手机 SFTP 用）。
--]]--
local Device = require("device")
local InfoMessage = require("ui/widget/infomessage")
local QRMessage = require("ui/widget/qrmessage")
local UIManager = require("ui/uimanager")
local WidgetContainer = require("ui/widget/container/widgetcontainer")
local _ = require("gettext")

local INFO_FILE = "/mnt/us/koreader/bookdrop_url.txt"

local Bookdrop = WidgetContainer:extend{
    name = "bookdrop",
    is_doc_only = false,
}

function Bookdrop:init()
    if self.ui and self.ui.menu then
        self.ui.menu:registerToMainMenu(self)
    end
end

function Bookdrop:getLines()
    local fh = io.open(INFO_FILE, "r")
    if not fh then return nil end
    local lines = {}
    for line in fh:lines() do
        line = line:match("^%s*(.-)%s*$")
        if line ~= "" then
            table.insert(lines, line)
        end
    end
    fh:close()
    return lines
end

function Bookdrop:showQR()
    local lines = self:getLines()
    if not lines or not lines[1] then
        UIManager:show(InfoMessage:new{
            text = _("还没有传书地址。\n\n请先在电脑上启动 Bookdrop（tools\\Start-Bookdrop.cmd），\n它会自动把地址同步到 Kindle，然后再点这里。"),
        })
        return
    end
    UIManager:show(QRMessage:new{
        text = lines[1],
        width = Device.screen:getWidth(),
        height = Device.screen:getHeight(),
    })
end

function Bookdrop:showInfo()
    local lines = self:getLines()
    if not lines then
        UIManager:show(InfoMessage:new{ text = _("还没有同步地址，请先在电脑上启动 Bookdrop。") })
        return
    end
    UIManager:show(InfoMessage:new{
        text = _("手机扫码传书页：\n") .. (lines[1] or "") .. "\n\n"
            .. _("手机 SFTP 直连：\n") .. (lines[2] or _("（未同步）")),
    })
end

function Bookdrop:addToMainMenu(menu_items)
    menu_items.bookdrop_qr = {
        text = _("传书二维码（手机扫码）"),
        sorting_hint = "tools",
        callback = function() self:showQR() end,
    }
    menu_items.bookdrop_info = {
        text = _("传书地址 / 手机 SFTP 信息"),
        sorting_hint = "tools",
        callback = function() self:showInfo() end,
    }
end

return Bookdrop
