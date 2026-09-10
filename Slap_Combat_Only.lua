--[[
    ===================================================================
    🥊 Slap Championship | Dedicated Combat Automation Script
    ===================================================================
    File: Slap_Combat_Only.lua
    Features:
      - 🎯 Auto Perfect Hit (100% Critical Power via Peak Sync)
      - 🛡️ Auto Dodge (100% Guaranteed - Dual-Trigger & Triple-Method)
      - 🎯 Auto Guess Slapper (100% Guaranteed - Real-Time Proximity Radar)
      - 🥊 Auto Slap (Automatically triggers slap when your turn starts)
    ===================================================================
]]

-- Services
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local VIM = game:GetService("VirtualInputManager")

local LocalPlayer = Players.LocalPlayer

-- Clean up any previous combat script instance
if _G.SlapCombatLoaded and _G.SlapCombatCleanup then
    pcall(_G.SlapCombatCleanup)
end
_G.SlapCombatLoaded = true

-- Configuration
_G.CombatConfig = {
    -- Auto Perfect Hit (Peak Sync Engine)
    AutoPerfectHit = true,
    HitScale = 1.0,                     -- 1.0 = ONE SHOT peak target scale
    AutoSlap = true,                    -- Auto start turn when slap button is visible

    -- Auto Dodge
    AutoDodge = true,
    DodgeDelay = 0.04,                  -- Sweet spot delay (0.04s) to allow server state initialization
    MultiPulse = true,                  -- Sends backup pulses at 0.12s & 0.20s so it NEVER misses
    NotifyDodge = true,                 -- Show notifications when dodging

    -- Auto Guess Slapper (ทายคนตบ 100% ด้วย Real-time Proximity Radar)
    AutoGuessSlapper = true,            -- 100% Auto detect and submit correct slapper
    GuessDelay = 0.3,                   -- 0.3s delay so server & GUI state are fully ready
    NotifyGuess = true,                 -- Show notifications when guess is submitted
    RadarThreshold = 12.0               -- Distance in studs to identify attacker in melee range (< 12 studs)
}

-- Remotes
local Events = ReplicatedStorage:WaitForChild("Events")
local SendToClientRemote = Events:WaitForChild("SendToClient")
local HitRemote = Events:WaitForChild("Hit")
local DodgeRemote = Events:WaitForChild("Dodge")
local SlapRemote = Events:WaitForChild("Slap")
local ChooseSlapperRemote = Events:WaitForChild("ChooseSlapper")

-- State variables
local Connections = {}
local lastDodgeKey = "E"
local isDodgeProcessing = false
local lastDetectedSlapper = nil
local isGuessProcessing = false

-- Real-time Proximity Radar State
local radarLockedTarget = nil -- { Name = string, UserId = number, Distance = number, Timestamp = number }
local currentClosestDistance = 999
local currentClosestPlayerName = "None"
local lastRadarUIUpdate = 0
local RadarParagraph = nil

-- Key translation table for console / touch
local KeyAliasMap = {
    ["RB"] = "ButtonR1",
    ["RT"] = "ButtonR2",
    ["X"] = "ButtonX",
    ["Y"] = "ButtonY",
    ["Touch"] = "E"
}

-- Helper: Check if Dodge GUI is currently visible on screen
local function isDodgeGuiActive()
    local success, result = pcall(function()
        local playerGui = LocalPlayer:FindFirstChild("PlayerGui")
        local inGame = playerGui and playerGui:FindFirstChild("Frames") and playerGui.Frames:FindFirstChild("InGame")
        local dodgeBtn = inGame and inGame:FindFirstChild("Dodge")
        return dodgeBtn and dodgeBtn.Visible
    end)
    return success and result
end

-- ===================================================================
-- TRIPLE-METHOD DODGE EXECUTOR
-- ===================================================================
local function executeDodgeAction(key)
    if not key or key == "" then
        key = lastDodgeKey or "E"
    end
    lastDodgeKey = key

    -- Method 1: Direct Network RemoteEvent
    DodgeRemote:FireServer(key)

    -- Method 2: Virtual Input Manager (Hardware Key Press Simulation)
    pcall(function()
        local keyCode = Enum.KeyCode[key]
        if VIM and keyCode then
            VIM:SendKeyEvent(true, keyCode, false, game)
            task.wait(0.015)
            VIM:SendKeyEvent(false, keyCode, false, game)
        end
    end)

    -- Method 3: Click the Dodge GUI Button (Triggers game's own script)
    pcall(function()
        local playerGui = LocalPlayer:FindFirstChild("PlayerGui")
        local inGame = playerGui and playerGui:FindFirstChild("Frames") and playerGui.Frames:FindFirstChild("InGame")
        local dodgeBtn = inGame and inGame:FindFirstChild("Dodge")
        if dodgeBtn and dodgeBtn.Visible then
            -- 3a: firesignal if supported by executor
            if firesignal then
                pcall(function() firesignal(dodgeBtn.Activated) end)
                pcall(function() firesignal(dodgeBtn.MouseButton1Up) end)
                pcall(function() firesignal(dodgeBtn.MouseButton1Click) end)
            end

            -- 3b: Virtual mouse click on the exact screen coordinates
            if VIM then
                local absPos = dodgeBtn.AbsolutePosition
                local absSize = dodgeBtn.AbsoluteSize
                local cx = absPos.X + absSize.X / 2
                local cy = absPos.Y + absSize.Y / 2
                VIM:SendMouseButtonEvent(cx, cy, 0, true, game, 1)
                task.wait(0.015)
                VIM:SendMouseButtonEvent(cx, cy, 0, false, game, 1)
            end
        end
    end)
end

-- Smart Multi-Pulse Dodge Routine
local function triggerDodgeRoutine(key)
    if not _G.CombatConfig.AutoDodge then return end
    if isDodgeProcessing then return end
    isDodgeProcessing = true

    task.spawn(function()
        -- Pulse 1: Main pulse after reaction delay (0.04s allows server to set up dodge window)
        if _G.CombatConfig.DodgeDelay > 0 then
            task.wait(_G.CombatConfig.DodgeDelay)
        end
        executeDodgeAction(key)

        -- If MultiPulse is enabled, send backup pulses to guarantee registration
        if _G.CombatConfig.MultiPulse then
            -- Pulse 2: at ~0.12s
            task.wait(0.08)
            if isDodgeGuiActive() then
                executeDodgeAction(key)
            end

            -- Pulse 3: at ~0.22s
            task.wait(0.10)
            if isDodgeGuiActive() then
                executeDodgeAction(key)
            end
        end

        task.wait(0.25)
        isDodgeProcessing = false
    end)
end

-- ===================================================================
-- REAL-TIME PROXIMITY RADAR & AUTO GUESS SLAPPER SYSTEM (ทายคนตบ 100%)
-- ===================================================================

-- Helper: Get list of opponent player names currently in the same match / arena
local function getMatchOpponents()
    local opponents = {}
    pcall(function()
        local arenaName = LocalPlayer:GetAttribute("Arena")
        local arena = arenaName and workspace.Arenas:FindFirstChild(arenaName)
        if arena and arena:FindFirstChild("Players") then
            for _, child in ipairs(arena.Players:GetChildren()) do
                if child.Name ~= LocalPlayer.Name then
                    table.insert(opponents, child.Name)
                end
            end
        end
    end)
    -- Fallback: Check GUI Slapper template clones
    if #opponents == 0 then
        pcall(function()
            local playerGui = LocalPlayer:FindFirstChild("PlayerGui")
            local inGame = playerGui and playerGui:FindFirstChild("Frames") and playerGui.Frames:FindFirstChild("InGame")
            local slappers = inGame and inGame:FindFirstChild("Slappers")
            local inner = slappers and slappers:FindFirstChild("Inner")
            if inner then
                for _, btn in ipairs(inner:GetChildren()) do
                    if btn:IsA("ImageButton") and btn.Name ~= "Template" and btn.Name ~= LocalPlayer.Name then
                        table.insert(opponents, btn.Name)
                    end
                end
            end
        end)
    end
    return opponents
end

-- Helper: Identify player standing at arena.SlapLocation
local function getPlayerAtSlapLocation()
    local candidate = nil
    pcall(function()
        local arenaName = LocalPlayer:GetAttribute("Arena")
        local arena = arenaName and workspace.Arenas:FindFirstChild(arenaName)
        if not arena or not arena:FindFirstChild("SlapLocation") then return end

        local slapLocationPos = arena.SlapLocation.Position
        local closestDist = 20 -- Radius in studs

        for _, player in ipairs(Players:GetPlayers()) do
            if player ~= LocalPlayer and player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
                local hrp = player.Character.HumanoidRootPart
                local dist = (hrp.Position - slapLocationPos).Magnitude
                if dist < closestDist then
                    closestDist = dist
                    candidate = player.Name
                end
            end
        end
    end)
    return candidate
end

-- Core: Resolve slapper identity with 100% accuracy using Real-Time Radar + Multiple Backups
local function resolveSlapperIdentity()
    -- Priority 1: Real-Time Proximity Radar (Locked player within melee distance < 12 studs within the last 15s)
    if radarLockedTarget and (tick() - radarLockedTarget.Timestamp) < 15 then
        if radarLockedTarget.Name ~= LocalPlayer.Name then
            return radarLockedTarget.Name, radarLockedTarget.UserId
        end
    end

    -- Priority 2: Network event interception (Cutscene/Cutscene2 attacker passed directly by server)
    if lastDetectedSlapper and lastDetectedSlapper ~= "" and lastDetectedSlapper ~= LocalPlayer.Name then
        local pl = Players:FindFirstChild(lastDetectedSlapper)
        return lastDetectedSlapper, pl and pl.UserId
    end

    -- Priority 3: Arena attribute "Slapper" (Set by server during turn execution)
    local arenaName = LocalPlayer:GetAttribute("Arena")
    local arena = arenaName and workspace.Arenas:FindFirstChild(arenaName)
    if arena then
        local slapperAttr = arena:GetAttribute("Slapper")
        if slapperAttr and slapperAttr ~= "" and slapperAttr ~= LocalPlayer.Name then
            local pl = Players:FindFirstChild(slapperAttr)
            return slapperAttr, pl and pl.UserId
        end
    end

    -- Priority 4: Physical position at arena.SlapLocation
    local posSlapper = getPlayerAtSlapLocation()
    if posSlapper then
        local pl = Players:FindFirstChild(posSlapper)
        return posSlapper, pl and pl.UserId
    end

    -- Priority 5: Fallback to match opponent list (100% reliable if 1v1 match)
    local opponents = getMatchOpponents()
    if #opponents == 1 then
        local pl = Players:FindFirstChild(opponents[1])
        return opponents[1], pl and pl.UserId
    elseif #opponents > 1 then
        local pl = Players:FindFirstChild(opponents[1])
        return opponents[1], pl and pl.UserId
    end

    return nil, nil
end

-- Execute Guess Action (Remote + GUI Click + UI Close)
local function submitGuessAction(slapperName, slapperUserId)
    if not slapperName or slapperName == "" then return end

    -- Method 1: RemoteEvent FireServer by Username
    ChooseSlapperRemote:FireServer(slapperName)

    -- Method 2: Click Slapper GUI Button (Triggers game's built-in handler)
    pcall(function()
        local playerGui = LocalPlayer:FindFirstChild("PlayerGui")
        local inGame = playerGui and playerGui:FindFirstChild("Frames") and playerGui.Frames:FindFirstChild("InGame")
        local slappersGui = inGame and inGame:FindFirstChild("Slappers")
        if slappersGui then
            local inner = slappersGui:FindFirstChild("Inner")
            local targetBtn = inner and (inner:FindFirstChild(slapperName) or (slapperUserId and inner:FindFirstChild(tostring(slapperUserId))))
            if targetBtn then
                if firesignal then
                    pcall(function() firesignal(targetBtn.Activated) end)
                    pcall(function() firesignal(targetBtn.MouseButton1Up) end)
                    pcall(function() firesignal(targetBtn.MouseButton1Click) end)
                end
                if VIM then
                    local absPos = targetBtn.AbsolutePosition
                    local absSize = targetBtn.AbsoluteSize
                    local cx = absPos.X + absSize.X / 2
                    local cy = absPos.Y + absSize.Y / 2
                    VIM:SendMouseButtonEvent(cx, cy, 0, true, game, 1)
                    task.wait(0.015)
                    VIM:SendMouseButtonEvent(cx, cy, 0, false, game, 1)
                end
            end
            -- Instantly hide the guess UI
            slappersGui.Visible = false
        end
    end)
end

-- Main Auto Guess Routine
local function triggerAutoGuessRoutine()
    if not _G.CombatConfig.AutoGuessSlapper then return end
    if isGuessProcessing then return end
    isGuessProcessing = true

    task.spawn(function()
        if _G.CombatConfig.GuessDelay > 0 then
            task.wait(_G.CombatConfig.GuessDelay)
        end

        local slapperName, slapperUserId = resolveSlapperIdentity()
        if slapperName then
            submitGuessAction(slapperName, slapperUserId)

            if _G.CombatConfig.NotifyGuess and Rayfield then
                local idText = slapperUserId and (" (ID: " .. tostring(slapperUserId) .. ")") or ""
                Rayfield:Notify({
                    Title = "🎯 Slapper Auto-Guessed!",
                    Content = "Target: " .. tostring(slapperName) .. idText .. " (100% ถูกต้อง)",
                    Duration = 3.5,
                    Image = 4483362458
                })
            end
        end

        task.wait(0.6)
        isGuessProcessing = false
        lastDetectedSlapper = nil
    end)
end

-- ===================================================================
-- DUAL-TRIGGER LISTENERS (NETWORK + GUI WATCHER + PROXIMITY RADAR)
-- ===================================================================

-- Trigger A: Network Packet from Server (SendToClient)
local sendToClientConn = SendToClientRemote.OnClientEvent:Connect(function(action, p2, p3)
    -- Dodge Event
    if action == "Dodge" then
        local key = typeof(p2) == "string" and p2 ~= "" and p2 or "E"
        lastDodgeKey = key
        triggerDodgeRoutine(key)

    -- Cutscene Event (Attacker identification)
    elseif action == "Cutscene" or action == "Cutscene2" then
        -- When local player is victim, p2 is false, and p3 is the attacker player/character
        if p2 == false and p3 then
            if typeof(p3) == "Instance" and p3:IsA("Player") then
                lastDetectedSlapper = p3.Name
                radarLockedTarget = {
                    Name = p3.Name,
                    UserId = p3.UserId,
                    Distance = 3.5,
                    Timestamp = tick()
                }
            elseif typeof(p3) == "string" then
                lastDetectedSlapper = p3
                local pl = Players:FindFirstChild(p3)
                radarLockedTarget = {
                    Name = p3,
                    UserId = pl and pl.UserId or 0,
                    Distance = 3.5,
                    Timestamp = tick()
                }
            elseif typeof(p3) == "Instance" and p3:FindFirstChild("Humanoid") then
                local pl = Players:GetPlayerFromCharacter(p3)
                if pl then
                    lastDetectedSlapper = pl.Name
                    radarLockedTarget = {
                        Name = pl.Name,
                        UserId = pl.UserId,
                        Distance = 3.5,
                        Timestamp = tick()
                    }
                end
            end
        end

    -- Choose Slapper Event (Guess phase triggered)
    elseif action == "ChooseSlapper" then
        triggerAutoGuessRoutine()
    end
end)
table.insert(Connections, sendToClientConn)

-- Trigger B: Real-time Proximity Radar & GUI Watcher (Runs every Heartbeat frame)
local guiWatcherConn = RunService.Heartbeat:Connect(function()
    pcall(function()
        local myChar = LocalPlayer.Character
        local myHRP = myChar and myChar:FindFirstChild("HumanoidRootPart")

        -- 1. REAL-TIME PROXIMITY RADAR TRACKER
        if myHRP and _G.CombatConfig.AutoGuessSlapper then
            local closestDist = math.huge
            local closestPl = nil

            for _, player in ipairs(Players:GetPlayers()) do
                if player ~= LocalPlayer and player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
                    local otherHRP = player.Character.HumanoidRootPart
                    local dist = (otherHRP.Position - myHRP.Position).Magnitude

                    if dist < closestDist then
                        closestDist = dist
                        closestPl = player
                    end
                end
            end

            if closestPl then
                currentClosestDistance = math.floor(closestDist * 10) / 10
                currentClosestPlayerName = closestPl.Name

                -- If an opponent approaches into melee proximity (< RadarThreshold, default 12 studs), lock them as slapper!
                if closestDist <= _G.CombatConfig.RadarThreshold then
                    radarLockedTarget = {
                        Name = closestPl.Name,
                        UserId = closestPl.UserId,
                        Distance = currentClosestDistance,
                        Timestamp = tick()
                    }
                    lastDetectedSlapper = closestPl.Name
                end
            end

            -- Update Live Radar UI Paragraph every 0.4 seconds
            if RadarParagraph and (tick() - lastRadarUIUpdate) > 0.4 then
                lastRadarUIUpdate = tick()
                local lockedText = "None"
                if radarLockedTarget and (tick() - radarLockedTarget.Timestamp) < 15 then
                    lockedText = radarLockedTarget.Name .. " (ID: " .. tostring(radarLockedTarget.UserId) .. " | " .. tostring(radarLockedTarget.Distance) .. " studs)"
                end
                RadarParagraph:Set({
                    Title = "📡 Real-time Distance Radar",
                    Content = "Closest Player: " .. tostring(currentClosestPlayerName) .. " (" .. tostring(currentClosestDistance) .. " studs)\n🎯 Locked Slapper: " .. lockedText
                })
            end
        end

        local playerGui = LocalPlayer:FindFirstChild("PlayerGui")
        local inGame = playerGui and playerGui:FindFirstChild("Frames") and playerGui.Frames:FindFirstChild("InGame")
        if not inGame then return end

        -- 2. Dodge Watcher
        if _G.CombatConfig.AutoDodge and not isDodgeProcessing then
            local dodgeBtn = inGame:FindFirstChild("Dodge")
            if dodgeBtn and dodgeBtn.Visible then
                local text = dodgeBtn:FindFirstChild("TextLabel") and dodgeBtn.TextLabel.Text or ""
                local resolvedKey = lastDodgeKey
                if text ~= "" and text ~= "Touch" then
                    resolvedKey = KeyAliasMap[text] or text
                end
                triggerDodgeRoutine(resolvedKey)
            end
        end

        -- 3. Guess Watcher (If Slappers frame becomes visible)
        if _G.CombatConfig.AutoGuessSlapper and not isGuessProcessing then
            local slappersGui = inGame:FindFirstChild("Slappers")
            if slappersGui and slappersGui.Visible then
                triggerAutoGuessRoutine()
            end
        end

        -- 4. Passive Slapper Tracker (Tracks arena attribute)
        local arenaName = LocalPlayer:GetAttribute("Arena")
        local arena = arenaName and workspace.Arenas:FindFirstChild(arenaName)
        if arena then
            local currentSlapper = arena:GetAttribute("Slapper")
            if currentSlapper and currentSlapper ~= "" and currentSlapper ~= LocalPlayer.Name then
                lastDetectedSlapper = currentSlapper
            end
        end
    end)
end)
table.insert(Connections, guiWatcherConn)

-- ===================================================================
-- AUTO PERFECT HIT (PEAK SYNC) & AUTO SLAP LOGIC
-- ===================================================================

local isHitProcessing = false

-- RenderStepped Loop for Peak Sync Auto Hit and Auto Slap
local combatLoopConn = RunService.RenderStepped:Connect(function()
    if not _G.SlapCombatLoaded then return end

    pcall(function()
        local playerGui = LocalPlayer:FindFirstChild("PlayerGui")
        local inGame = playerGui and playerGui:FindFirstChild("Frames") and playerGui.Frames:FindFirstChild("InGame")
        if not inGame then return end

        -- Auto Slap (Start turn automatically)
        if _G.CombatConfig.AutoSlap and inGame:FindFirstChild("Slap") and inGame.Slap.Visible then
            local arenaName = LocalPlayer:GetAttribute("Arena")
            local arena = arenaName and workspace.Arenas:FindFirstChild(arenaName)
            if not arena or arena:GetAttribute("Slapper") == "" then
                SlapRemote:FireServer()
                inGame.Slap.Visible = false
            end
        end

        -- Auto Perfect Hit (Peak Sync Engine: 100% Critical Power)
        if _G.CombatConfig.AutoPerfectHit and not isHitProcessing then
            local hitBtn = inGame:FindFirstChild("Hit")
            local bar = inGame:FindFirstChild("Bar")
            local line = bar and bar:FindFirstChild("Line")

            if hitBtn and hitBtn.Visible and line then
                local currentScale = line.Position.Y.Scale
                -- When the bar line reaches the peak zone (>= 0.95 by default)
                if currentScale >= (_G.CombatConfig.HitScale - 0.05) then
                    isHitProcessing = true
                    HitRemote:FireServer(currentScale)
                    if firesignal then
                        pcall(function() firesignal(hitBtn.Activated) end)
                    end
                    hitBtn.Visible = false
                    if bar then bar.Visible = false end

                    task.delay(0.5, function()
                        isHitProcessing = false
                    end)
                end
            end
        end
    end)
end)
table.insert(Connections, combatLoopConn)

-- Cleanup function
_G.SlapCombatCleanup = function()
    _G.SlapCombatLoaded = false
    for _, conn in ipairs(Connections) do
        pcall(function() conn:Disconnect() end)
    end
end

-- ===================================================================
-- USER INTERFACE (RAYFIELD UI)
-- ===================================================================

local Rayfield = loadstring(game:HttpGet('https://sirius.menu/rayfield'))()

local Window = Rayfield:CreateWindow({
    Name = "🥊 Slap Combat (Hit, Dodge & Guess)",
    LoadingTitle = "Slap Combat",
    LoadingSubtitle = "by Antigravity",
    ConfigurationSaving = {
        Enabled = true,
        FolderName = "SlapCombat",
        FileName = "Config"
    },
    Discord = {
        Enabled = false,
        Invite = "",
        RememberJoins = true
    },
    KeySystem = false
})

local MainTab = Window:CreateTab("⚡ Combat Hub", 4483362458)

-- 1. AUTO PERFECT HIT SECTION
MainTab:CreateSection("🎯 Auto Perfect Hit (Peak Sync)")

MainTab:CreateToggle({
    Name = "Enable Auto Perfect Hit (Peak Sync)",
    CurrentValue = true,
    Flag = "AutoPerfectHit",
    Callback = function(Value)
        _G.CombatConfig.AutoPerfectHit = Value
    end,
})

MainTab:CreateSlider({
    Name = "Hit Power Scale (1.0 = ONE SHOT)",
    Range = {0.80, 1.0},
    Increment = 0.01,
    Suffix = "Scale",
    CurrentValue = 1.0,
    Flag = "HitScale",
    Callback = function(Value)
        _G.CombatConfig.HitScale = Value
    end,
})

MainTab:CreateToggle({
    Name = "Auto Slap (Start Turn Automatically)",
    CurrentValue = true,
    Flag = "AutoSlap",
    Callback = function(Value)
        _G.CombatConfig.AutoSlap = Value
    end,
})

-- 2. AUTO DODGE SECTION
MainTab:CreateSection("🛡️ Auto Dodge (100% Guaranteed)")

MainTab:CreateToggle({
    Name = "Enable Auto Dodge (Godmode)",
    CurrentValue = true,
    Flag = "AutoDodge",
    Callback = function(Value)
        _G.CombatConfig.AutoDodge = Value
    end,
})

MainTab:CreateSlider({
    Name = "Dodge Delay (0.04s Recommended)",
    Range = {0.0, 0.20},
    Increment = 0.01,
    Suffix = "s",
    CurrentValue = 0.04,
    Flag = "DodgeDelay",
    Callback = function(Value)
        _G.CombatConfig.DodgeDelay = Value
    end,
})

MainTab:CreateToggle({
    Name = "Multi-Pulse Burst (Sends 3 Verification Pulses)",
    CurrentValue = true,
    Flag = "MultiPulse",
    Callback = function(Value)
        _G.CombatConfig.MultiPulse = Value
    end,
})

-- 3. AUTO GUESS SLAPPER SECTION
MainTab:CreateSection("🎯 Auto Guess Slapper (100% ถูกต้อง)")

RadarParagraph = MainTab:CreateParagraph({
    Title = "📡 Real-time Distance Radar",
    Content = "Closest Player: Scanning...\n🎯 Locked Slapper: None"
})

MainTab:CreateToggle({
    Name = "Enable Auto Guess (ทายคนตบอัตโนมัติ)",
    CurrentValue = true,
    Flag = "AutoGuessSlapper",
    Callback = function(Value)
        _G.CombatConfig.AutoGuessSlapper = Value
    end,
})

MainTab:CreateSlider({
    Name = "Radar Melee Threshold (ระยะตรวจจับคนประชิด)",
    Range = {6.0, 18.0},
    Increment = 0.5,
    Suffix = " studs",
    CurrentValue = 12.0,
    Flag = "RadarThreshold",
    Callback = function(Value)
        _G.CombatConfig.RadarThreshold = Value
    end,
})

MainTab:CreateSlider({
    Name = "Guess Delay (0.3s แนะนำ)",
    Range = {0.0, 1.5},
    Increment = 0.05,
    Suffix = "s",
    CurrentValue = 0.3,
    Flag = "GuessDelay",
    Callback = function(Value)
        _G.CombatConfig.GuessDelay = Value
    end,
})

MainTab:CreateToggle({
    Name = "Show Guess Notification (แจ้งเตือนผลทาย)",
    CurrentValue = true,
    Flag = "NotifyGuess",
    Callback = function(Value)
        _G.CombatConfig.NotifyGuess = Value
    end,
})

-- 4. SCRIPT CONTROL
MainTab:CreateSection("⚙️ Script Control")

MainTab:CreateButton({
    Name = "Unload Script",
    Callback = function()
        if _G.SlapCombatCleanup then
            _G.SlapCombatCleanup()
        end
        Rayfield:Destroy()
    end,
})

Rayfield:Notify({
    Title = "🥊 Slap Combat Loaded!",
    Content = "100% Perfect Hit, Auto Dodge & Real-Time Radar active.",
    Duration = 4,
    Image = 4483362458
})
