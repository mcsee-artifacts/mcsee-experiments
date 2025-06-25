#include <cstdint>

#pragma once

namespace memory {

class function {
public:
    function(uint64_t function) : m_function(function) {}

    bool apply_to(uint64_t addr) const {
        return __builtin_parityll(addr & m_function);
    }

    // Auto-conversion operator.
    operator uint64_t() const { return m_function; }

private:
    uint64_t m_function { 0 };
};

class function_constraint {
public:
    function_constraint(function function, bool value) : m_function(function), m_value(value) {};

    [[nodiscard]] bool is_satisfied_by(uint64_t addr) const {
        return m_function.apply_to(addr) == m_value;
    }

    [[nodiscard]] function const& func() const { return m_function; }
    [[nodiscard]] bool value() const { return m_value; }

private:
    function m_function;
    bool m_value { false };
};


}