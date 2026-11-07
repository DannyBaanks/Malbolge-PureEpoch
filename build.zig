const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // Módulo principal de Malbolge
    const malbolge_mod = b.addModule("malbolge", .{
        .root_source_file = b.path("src/malbolge.zig"),
        .target = target,
        .optimize = optimize,
    });

    // Módulo de pruebas
    const test_mod = b.createModule(.{
        .root_source_file = b.path("test_suite.zig"),
        .target = target,
        .optimize = optimize,
    });
    test_mod.addImport("malbolge", malbolge_mod);

    // Ejecutable de tests
    const test_exe = b.addTest(.{
        .root_module = test_mod,
    });

    const run_test = b.addRunArtifact(test_exe);
    const test_step = b.step("test", "Run PureEpoch Zig test suite");
    test_step.dependOn(&run_test.step);
}
