#include "allocation.hpp"
#include <cstddef>
#include <string>

#pragma once

class dram_address {
public:
    static void initialize(allocation alloc);
    static allocation& alloc();

    [[nodiscard]] static dram_address from_virt(volatile char* virt);

    dram_address(size_t subchannel, size_t rank, size_t bank_group, size_t bank, size_t row, size_t column)
        : m_subchannel(subchannel), m_rank(rank), m_bank_group(bank_group), m_bank(bank), m_row(row), m_column(column) {}

    [[nodiscard]] volatile char* to_virt() const;

    [[nodiscard]] size_t subchannel() const;
    [[nodiscard]] size_t rank() const;
    [[nodiscard]] size_t bank_group() const;
    [[nodiscard]] size_t bank() const;
    [[nodiscard]] size_t row() const;
    [[nodiscard]] size_t column() const;

    void add_inplace(size_t subchannels, size_t ranks, size_t bank_groups, size_t banks, size_t rows, size_t columns);
    dram_address add(size_t subchannels, size_t ranks, size_t bank_groups, size_t banks, size_t rows, size_t columns) {
        auto tmp = *this;
        tmp.add_inplace(subchannels, ranks, bank_groups, banks, rows, columns);
        return tmp;
    }

    [[nodiscard]] std::string to_string() const;
private:
    size_t m_subchannel {};
    size_t m_rank {};
    size_t m_bank_group {};
    size_t m_bank {};
    size_t m_row {};
    size_t m_column {};
};