#include "program.hpp"
#include "../memory/dram_address.hpp"
#include "../utils.hpp"

#include <cstdio>

namespace program {

void program::write_to(FILE* fp) const {
    if (m_instructions.empty()) {
        fprintf(fp, "(empty)\n");
    } else {
        for (auto const& inst : m_instructions) {
            switch (inst.type()) {
                case instruction_type::nop:
                    fprintf(fp, "NOP\n");
                    break;
                case instruction_type::read:
                case instruction_type::write:
                case instruction_type::clflush: {
                    auto dram_addr = dram_address::from_virt(inst.addr()).to_string();
                    if (inst.type() == instruction_type::read) {
                        fprintf(fp, "READ");
                    } else if (inst.type() == instruction_type::write) {
                        fprintf(fp, "WRITE");
                    } else if (inst.type() == instruction_type::clflush) {
                        fprintf(fp, "CLFLUSH");
                    } else {
                        assert(false && "Unreachable.");
                    }
                    fprintf(fp, " %s\n", dram_addr.c_str());
                    break;
                }
                case instruction_type::mfence:
                    fprintf(fp, "MFENCE\n");
                    break;
            }
        }
    }
}

void program::write_to_file(char const* path) const {
    FILE* fp = fopen(path, "w");
    if (!fp) {
        perror("fopen");
        _printf("Error: Could not write_to program to file '%s'.", path);
        exit(EXIT_FAILURE);
    }

    write_to(fp);
    fclose(fp);
}

}
