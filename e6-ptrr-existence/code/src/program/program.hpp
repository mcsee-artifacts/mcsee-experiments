#include "instruction.hpp"

#include <vector>

#pragma once

namespace program {

class program {
public:
    program() = default;

    [[nodiscard]] std::vector<instruction> const& instructions() const { return m_instructions; }

    void add_instruction(instruction inst) {
        m_instructions.push_back(std::move(inst));
    }

    void execute() const {
        for (auto const& inst : m_instructions) {
            inst.execute();
        }
    }

    void write_to(FILE* fp) const;
    void write_to_file(char const* path) const;
private:
    std::vector<instruction> m_instructions;
};

}
