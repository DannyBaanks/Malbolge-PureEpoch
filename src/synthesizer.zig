const std = @import("std");
const mal = @import("malbolge.zig");

pub const SearchTarget = struct {
    expected_output: []const u8,
    require_halt: bool = true,
    max_steps: usize = 5000,
};

pub const SearchResult = struct {
    found: bool,
    candidates_evaluated: usize,
    solution_bytes: [256]u8,
    solution_len: usize,
    steps_taken: usize,
    terminal: mal.Terminal,
};

/// High-throughput in-memory synthesizer and candidate explorer.
pub const Synthesizer = struct {
    pub fn init() Synthesizer {
        return .{};
    }

    /// Search by mutating designated slot positions in a template program.
    pub fn searchSlot(
        self: *Synthesizer,
        template: []const u8,
        slot_pos: usize,
        allowed_ops: []const u8,
        target: SearchTarget,
    ) SearchResult {
        _ = self;
        var evaluated: usize = 0;
        var buf: [256]u8 = undefined;
        if (template.len > buf.len) {
            return .{
                .found = false,
                .candidates_evaluated = 0,
                .solution_bytes = undefined,
                .solution_len = 0,
                .steps_taken = 0,
                .terminal = .STALL,
            };
        }
        @memcpy(buf[0..template.len], template);

        // Iterate through all candidate bytes for slot_pos
        for (allowed_ops) |op| {
            // Find a byte that decodes to `op` at `slot_pos`
            var byte_val: u8 = 33;
            while (byte_val <= 126) : (byte_val += 1) {
                if (mal.XLAT1[(byte_val - 33 + slot_pos) % 94] == op) {
                    buf[slot_pos] = byte_val;
                    evaluated += 1;

                    var vm = mal.Machine.init();
                    if (vm.loadProgram(buf[0..template.len])) |_| {
                        vm.run("", target.max_steps);
                        const out = vm.getOutput();

                        var matches = true;
                        if (target.require_halt and vm.terminal != .HALT) {
                            matches = false;
                        }
                        if (target.expected_output.len > 0 and !std.mem.eql(u8, out, target.expected_output)) {
                            matches = false;
                        }

                        if (matches) {
                            var sol: [256]u8 = undefined;
                            @memcpy(sol[0..template.len], buf[0..template.len]);
                            return .{
                                .found = true,
                                .candidates_evaluated = evaluated,
                                .solution_bytes = sol,
                                .solution_len = template.len,
                                .steps_taken = vm.steps,
                                .terminal = vm.terminal,
                            };
                        }
                    } else |_| {}
                }
            }
        }

        return .{
            .found = false,
            .candidates_evaluated = evaluated,
            .solution_bytes = undefined,
            .solution_len = 0,
            .steps_taken = 0,
            .terminal = .STALL,
        };
    }
};
