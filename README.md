# AI-native-Modlist-Profile-Builder
Build-system-first платформа для управляемых сборок Skyrim, в которой AI-контур отвечает за планирование/диагностику, а все side-effects выполняются только через deterministic executor (allowlist, capability checks), с фиксацией Plan IR/Lockfile/Provenance/Job Journal и политикой “без bundling/redistributing модов”.
