const std = @import("std");

pub const MEM_SIZE: usize = 59049;

pub const XLAT1 = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha";
pub const XLAT2 = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@";

pub const TRITS = [3][3]u16{
    .{ 1, 0, 0 },
    .{ 1, 0, 2 },
    .{ 2, 2, 1 },
};

pub fn crazy(x_in: u16, y_in: u16) u16 {
    var x = x_in;
    var y = y_in;
    var n: u16 = 0;
    var power: u16 = 1;
    var i: usize = 0;
    while (i < 10) : (i += 1) {
        const x_trit: usize = @intCast(x % 3);
        const y_trit: usize = @intCast(y % 3);
        n += TRITS[y_trit][x_trit] * power;
        x /= 3;
        y /= 3;
        if (i < 9) power *= 3;
    }
    return n;
}

pub fn rot1(val: u16) u16 {
    return (val / 3) + (val % 3) * 19683;
}

pub fn isValidInstruction(ch: u8) bool {
    return switch (ch) {
        'j', 'i', '*', 'p', '<', '/', 'v', 'o' => true,
        else => false,
    };
}

pub const LoadError = error{
    NonAsciiPrintable,
    StrictLoaderRejected,
    ProgramTooShort,
    ProgramTooLarge,
};

pub fn load(source: []const u8, mem: *[MEM_SIZE]u16) LoadError!usize {
    var len: usize = 0;
    for (source) |byte| {
        // Ignorar espacios en blanco según la especificación clásica de Olmstead
        if (byte == ' ' or byte == '\t' or byte == '\n' or byte == '\r' or byte == 11 or byte == 12) {
            continue;
        }
        if (byte < 33 or byte > 126) {
            return error.NonAsciiPrintable;
        }
        const inst_idx = (byte - 33 + len) % 94;
        const inst = XLAT1[inst_idx];
        if (!isValidInstruction(inst)) {
            return error.StrictLoaderRejected;
        }
        if (len >= MEM_SIZE) {
            return error.ProgramTooLarge;
        }
        mem[len] = byte;
        len += 1;
    }
    if (len < 2) {
        return error.ProgramTooShort;
    }
    var i: usize = len;
    while (i < MEM_SIZE) : (i += 1) {
        mem[i] = crazy(mem[i - 1], mem[i - 2]);
    }
    return len;
}

pub const Terminal = enum {
    RUNNING,
    HALT,
    STALL,
    BUDGET,
};

pub const Machine = struct {
    mem: [MEM_SIZE]u16,
    a: u16 = 0,
    c: u16 = 0,
    d: u16 = 0,
    steps: usize = 0,
    terminal: Terminal = .RUNNING,
    input_cursor: usize = 0,
    output_buf: [131072]u8 = undefined,
    output_len: usize = 0,

    pub fn init() Machine {
        return .{
            .mem = [_]u16{0} ** MEM_SIZE,
            .output_buf = undefined,
            .output_len = 0,
        };
    }

    pub fn loadProgram(self: *Machine, source: []const u8) LoadError!usize {
        return load(source, &self.mem);
    }

    pub fn getOutput(self: *const Machine) []const u8 {
        return self.output_buf[0..self.output_len];
    }

    pub fn step(self: *Machine, payload: []const u8) void {
        if (self.terminal != .RUNNING) return;
        const pc = self.c;
        const v = self.mem[pc];
        if (v < 33 or v > 126) {
            self.terminal = .STALL;
            return;
        }
        const inst_idx = (v - 33 + pc) % 94;
        const instruction = XLAT1[inst_idx];

        switch (instruction) {
            'j' => {
                self.d = self.mem[self.d];
            },
            'i' => {
                self.c = self.mem[self.d];
            },
            '*' => {
                const old = self.mem[self.d];
                const rotated = rot1(old);
                self.mem[self.d] = rotated;
                self.a = rotated;
            },
            'p' => {
                const old = self.mem[self.d];
                const res = crazy(self.a, old);
                self.mem[self.d] = res;
                self.a = res;
            },
            '<' => {
                if (self.output_len < self.output_buf.len) {
                    self.output_buf[self.output_len] = @truncate(self.a & 0xFF);
                    self.output_len += 1;
                }
            },
            '/' => {
                if (self.input_cursor < payload.len) {
                    self.a = payload[self.input_cursor];
                    self.input_cursor += 1;
                } else {
                    self.a = 59048;
                }
            },
            'v' => {
                self.terminal = .HALT;
                return;
            },
            'o' => {},
            else => {},
        }

        const old = self.mem[self.c];
        if (old < 33 or old > 126) {
            self.terminal = .STALL;
            return;
        }
        self.mem[self.c] = XLAT2[old - 33];
        self.c = @intCast((self.c + 1) % MEM_SIZE);
        self.d = @intCast((self.d + 1) % MEM_SIZE);
        self.steps += 1;
    }

    pub fn run(self: *Machine, payload: []const u8, max_steps: usize) void {
        while (self.terminal == .RUNNING and self.steps < max_steps) {
            self.step(payload);
        }
        if (self.terminal == .RUNNING) {
            self.terminal = .BUDGET;
        }
    }
};
