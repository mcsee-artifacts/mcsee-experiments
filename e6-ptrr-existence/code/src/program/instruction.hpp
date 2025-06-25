#include "../utils.hpp"
#include <cassert>

#pragma once

namespace program {

enum class instruction_type {
    nop,
    read,
    write,
    clflush,
    mfence
};

class instruction {
public:
    static instruction nop() { return { instruction_type::nop, nullptr }; };
    static instruction read(volatile char* addr) { return { instruction_type::read, addr }; }
    static instruction write(volatile char* addr) { return { instruction_type::write, addr }; }
    static instruction clflush(volatile char* addr) { return { instruction_type::clflush, addr }; }
    static instruction mfence() { return { instruction_type::mfence, nullptr }; }

    [[gnu::always_inline]] void execute() const {
        switch (m_type) {
            case instruction_type::nop:
                return;
            case instruction_type::read:
                *m_addr;
                return;
            case instruction_type::write:
                *m_addr = s_counter++;
                return;
            case instruction_type::clflush:
                clflushopt(m_addr);
                return;
            case instruction_type::mfence:
                mfence();
                return;
        }
    }

    [[nodiscard]] instruction_type type() const { return m_type; }
    [[nodiscard]] volatile char* addr() const {
        assert(m_type == instruction_type::read || m_type == instruction_type::write || m_type == instruction_type::clflush);
        return m_addr;
    }
private:
    instruction(instruction_type type, volatile char* addr)
        : m_type(type), m_addr(addr) {
        if (type == instruction_type::read || type == instruction_type::write || type == instruction_type::clflush) {
            assert(addr);
        } else {
            assert(!addr);
        }
    }

    static char s_counter;

    instruction_type m_type { instruction_type::nop };
    volatile char* m_addr;
};

}
