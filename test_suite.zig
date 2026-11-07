const std = @import("std");
const testing = std.testing;
const mal = @import("src/malbolge.zig");

test "Algebra: Crazy Involution at 121" {
    var b: u16 = 0;
    while (b < 256) : (b += 1) {
        const ciphered = mal.crazy(b, 121);
        const deciphered = mal.crazy(ciphered, 121);
        try testing.expectEqual(b, deciphered);
    }
}

test "Boss 1: Cascade Byzantine Fault Rollback (J1 -> J2)" {
    const src = @embedFile("candidates/boss1_byzantine.mal");
    var vm = mal.Machine.init();
    _ = try vm.loadProgram(src);

    // Initial 1, cand 1, cand 1 -> S
    vm.run(&[_]u8{ 1, 1, 1 }, 50000);
    try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
    try testing.expect(vm.getOutput().len > 0);
}

test "Boss 2: Brainfuck Linear Subset to Malbolge" {
    const src = @embedFile("candidates/boss2_brainfuck.mal");
    var vm = mal.Machine.init();
    _ = try vm.loadProgram(src);

    vm.run("", 50000);
    try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
}

test "Boss 3: Real Autonomous Loop with Repeated PC" {
    const src = @embedFile("candidates/boss3_real_loop.mal");

    // Para N = 2 -> emite "11"
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("2", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("11", vm.getOutput());
    }

    // Para N = 0 -> emite ""
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("0", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("", vm.getOutput());
    }
}

test "Boss 4: Wolfram Rule 90 Sierpinski Triangle (v3 CA)" {
    const src = @embedFile("candidates/boss4_v3_ca.mal");
    var vm = mal.Machine.init();
    _ = try vm.loadProgram(src);

    vm.run("1", 50000);
    try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
    try testing.expect(vm.getOutput().len > 0);
}

test "Boss 5: Cat Real (Transparent Streaming & Clean EOF Halt)" {
    const src = @embedFile("candidates/cat_real.mal");

    // Flujo normal
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("PURE_EPOCH_ZIG\n", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("PURE_EPOCH_ZIG\n", vm.getOutput());
    }

    // Flujo vacío -> parada inmediata con 0 salida
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("", vm.getOutput());
    }
}

test "Boss 6: Rev Real (LIFO Stack Stream Inversion)" {
    const src = @embedFile("candidates/rev_real.mal");

    // Pares invertidos
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("AB", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("BA", vm.getOutput());
    }

    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("12", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("21", vm.getOutput());
    }

    // Byte único
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("Z", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("Z", vm.getOutput());
    }

    // Vacío
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("", vm.getOutput());
    }
}

test "Boss 7: Wc Real (Stream Byte Counter)" {
    const src = @embedFile("candidates/wc_real.mal");

    // Longitud 3+ -> emite '3'
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("12345", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("3", vm.getOutput());
    }

    // Longitud 2 -> emite '2'
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("AB", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("2", vm.getOutput());
    }

    // Longitud 1 -> emite '1'
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("X", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("1", vm.getOutput());
    }

    // Longitud 0 -> emite '0'
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("0", vm.getOutput());
    }
}

test "Boss 8: Cmp Real (Stream Equality Predicate)" {
    const src = @embedFile("candidates/cmp_real.mal");

    // Iguales
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("==", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("=", vm.getOutput());
    }

    // Desiguales
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("!=", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("!", vm.getOutput());
    }
}

test "Boss 9: Add Real (In-VM Ternary Arithmetic ALU)" {
    const src = @embedFile("candidates/add_real.mal");

    // Caso 1 + 1 = 2
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("11", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("2", vm.getOutput());
    }

    // Caso 0 + 1 = 1
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("01", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("1", vm.getOutput());
    }

    // Caso 0 + 0 = 0
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("00", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("0", vm.getOutput());
    }
}

test "Boss 10: Sort2 Real (Conditional Bubble / Min-Max Sorter)" {
    const src = @embedFile("candidates/sort2_real.mal");

    // Invertidos -> ordenados
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("10", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("01", vm.getOutput());
    }

    // Ya ordenados -> preservados
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("01", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("01", vm.getOutput());
    }
}

test "Boss 11: Reloj Real (4-Tick Digital Stopwatch)" {
    const src = @embedFile("candidates/reloj_real.mal");

    // 3 pulsos
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("PPP", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("00:00\n00:01\n00:02\n", vm.getOutput());
    }

    // 0 pulsos
    {
        var vm = mal.Machine.init();
        _ = try vm.loadProgram(src);
        vm.run("", 50000);
        try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
        try testing.expectEqualStrings("", vm.getOutput());
    }
}

test "Boss 12: Reloj Infinito (60s In-VM Digital Clock 00:00..00:59)" {
    const src = @embedFile("candidates/reloj_infinito.mal");
    var vm = mal.Machine.init();
    _ = try vm.loadProgram(src);

    // Ejecución autónoma completa de 60 segundos
    vm.run("", 50000);
    try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
    try testing.expectEqual(@as(usize, 16660), vm.steps);

    const out = vm.getOutput();
    // 60 líneas de formato "00:XX\n" = 60 * 6 = 360 bytes
    try testing.expectEqual(@as(usize, 360), out.len);
    try testing.expectEqualStrings("00:00\n", out[0..6]);
    try testing.expectEqualStrings("00:59\n", out[354..360]);
}

test "Boss 13: In-VM BCD Ripple-Carry (00:59 -> 01:00)" {
    const src = @embedFile("candidates/boss13_reloj_carry.mal");
    var vm = mal.Machine.init();
    _ = try vm.loadProgram(src);

    // Registros iniciales antes de ejecución
    try testing.expectEqual(@as(u16, '0'), vm.mem[50]); // M10
    try testing.expectEqual(@as(u16, '0'), vm.mem[51]); // M1
    try testing.expectEqual(@as(u16, '5'), vm.mem[45]); // S10
    try testing.expectEqual(@as(u16, '9'), vm.mem[41]); // S1

    vm.run("", 50000);

    try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
    try testing.expectEqualStrings("00:59\n01:00\n", vm.getOutput());
    try testing.expectEqual(@as(usize, 1806), vm.steps);

    // Registros después de la computación aritmética in-VM
    try testing.expectEqual(@as(u16, '0'), vm.mem[50]); // M10
    try testing.expectEqual(@as(u16, '1'), vm.mem[51]); // M1 (Acarreo absorbido)
    try testing.expectEqual(@as(u16, '0'), vm.mem[45]); // S10 (Rollover mod 60)
    try testing.expectEqual(@as(u16, '0'), vm.mem[41]); // S1  (Rollover 9->0)
}

test "Fail-Closed: Mutants Detection" {
    // 1. Broken loader mutant must be rejected at load time
    const broken_loader_src = @embedFile("candidates/reloj_carry_broken_loader.mal");
    var vm1 = mal.Machine.init();
    try testing.expectError(mal.LoadError.StrictLoaderRejected, vm1.loadProgram(broken_loader_src));

    // 2. Broken EOF mutant fails to halt cleanly on EOF
    const broken_eof_src = @embedFile("candidates/reloj_carry_broken_eof.mal");
    var vm2 = mal.Machine.init();
    _ = try vm2.loadProgram(broken_eof_src);
    vm2.run("", 50000);
    try testing.expect(vm2.terminal != mal.Terminal.HALT);
}

test "ABI: Mutant NOP Execution and Post-Encryption" {
    var vm = mal.Machine.init();
    // Simulate non-operator ASCII character in cell 0 ('E')
    vm.mem[0] = 'E';
    vm.step("");
    try testing.expectEqual(mal.Terminal.RUNNING, vm.terminal);
    try testing.expectEqual(@as(u16, 1), vm.c);
    try testing.expectEqual(@as(u16, 1), vm.d);
    try testing.expectEqual(@as(u16, mal.XLAT2['E' - 33]), vm.mem[0]);
}

test "ABI: Canonical EOF Handling" {
    var vm = mal.Machine.init();
    // Two instructions: '/' (input) at 0, 'v' (halt) at 1
    // Find valid source bytes for '/' and 'v'
    var b0: u8 = 33;
    while (b0 <= 126) : (b0 += 1) {
        if (mal.XLAT1[(b0 - 33 + 0) % 94] == '/') break;
    }
    var b1: u8 = 33;
    while (b1 <= 126) : (b1 += 1) {
        if (mal.XLAT1[(b1 - 33 + 1) % 94] == 'v') break;
    }
    const prog = [_]u8{ b0, b1 };
    _ = try vm.loadProgram(&prog);
    vm.run("", 10);
    try testing.expectEqual(mal.Terminal.HALT, vm.terminal);
    try testing.expectEqual(@as(u16, 59048), vm.a);
}

test "Synthesizer: High-Throughput Slot Search" {
    const syn = @import("src/synthesizer.zig");
    var s = syn.Synthesizer.init();
    
    // Template with 2 bytes: byte 0 is wildcard, byte 1 is 'v' (halt)
    var b1: u8 = 33;
    while (b1 <= 126) : (b1 += 1) {
        if (mal.XLAT1[(b1 - 33 + 1) % 94] == 'v') break;
    }
    const template = [_]u8{ 'o', b1 };

    const res = s.searchSlot(&template, 0, "ov", .{
        .expected_output = "",
        .require_halt = true,
        .max_steps = 10,
    });

    try testing.expect(res.found);
    try testing.expect(res.candidates_evaluated > 0);
    try testing.expectEqual(mal.Terminal.HALT, res.terminal);
}
