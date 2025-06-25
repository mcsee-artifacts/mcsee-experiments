#include "config.hpp"
#include "dram_address.hpp"
#include "../utils.hpp"

#include <array>
#include <cassert>

#if ZEN3
#define MATRIX_SIZE 28
#else
#define MATRIX_SIZE 30
#endif
#define MATRIX_MASK ((1ULL << MATRIX_SIZE) - 1)

using matrix_t = std::array<size_t, MATRIX_SIZE>;

static allocation* s_alloc;
static struct {
    size_t phys_linear_offset {};

    size_t subchannel_shift {};
    size_t subchannel_mask {};
    size_t rank_shift {};
    size_t rank_mask {};
    size_t bank_group_shift {};
    size_t bank_group_mask {};
    size_t bank_shift {};
    size_t bank_mask {};
    size_t row_shift {};
    size_t row_mask {};
    size_t column_shift {};
    size_t column_mask {};

    matrix_t linear_to_dram_matrix {};
    matrix_t dram_to_linear_matrix {};
} s_config;

static void print_matrix(matrix_t const& matrix) {
    for (size_t i = 0; i < MATRIX_SIZE; i++) {
        for (size_t j = 0; j < MATRIX_SIZE; j++) {
            printf("%lu ", (matrix[i] >> j) & 1);
        }
        printf("\n");
    }
}

static size_t apply_matrix(matrix_t const& matrix, size_t addr) {
    size_t result = 0;
    for (size_t i = 0; i < MATRIX_SIZE; i++) {
        auto bit = __builtin_parityll(matrix[i] & addr);
        if (bit) {
            result |= BIT_SET(i);
        }
    }
    return result;
}

static matrix_t compute_inverse(matrix_t input) {
    // Set result to the identity matrix.
    matrix_t result {};
    for (size_t i = 0; i < MATRIX_SIZE; i++) {
        result[i] = BIT_SET(i);
    }

    // STEP 1: Gauss elimination.
    for (size_t i = 0; i < MATRIX_SIZE; i++) {
        size_t pivot = -1;
        for (size_t j = i; j < MATRIX_SIZE; j++) {
            if (input[j] & BIT_SET(i)) {
                pivot = j;
                break;
            }
        }

        if (pivot == (size_t)-1) {
            _printf("Could not compute matrix inverse as input matrix is singular.");
            exit(EXIT_FAILURE);
        }

        // Swap rows to get pivot into i-th row.
        std::swap(input[i], input[pivot]);
        std::swap(result[i], result[pivot]);

        // Now, input[i] has bit i set. Unset the bit in all functions below using XOR.
        for (size_t j = i + 1; j < MATRIX_SIZE; j++) {
            if (input[j] & BIT_SET(i)) {
                input[j] ^= input[i];
                result[j] ^= result[i];
            }
        }
    }
    // Now, input is upper triangular.

    // STEP 2: Unset all bits not on the diagonal, starting from the bottom.
    for (ssize_t i = MATRIX_SIZE - 1; i >= 0; i--) {
        for (ssize_t j = 0; j < i; j++) {
            if (input[j] & BIT_SET(i)) {
                input[j] ^= input[i];
                result[j] ^= result[i];
            }
        }
    }

    // Check that input is now the identity matrix.
    for (size_t i = 0; i < MATRIX_SIZE; i++) {
        assert(input[i] == BIT_SET(i));
    }

    return result;
}

static void initialize_config() {
    size_t phys_linear_offset = 0;
    std::vector<size_t> subchannel_funcs;
    std::vector<size_t> rank_funcs;
    std::vector<size_t> bank_group_funcs;
    std::vector<size_t> bank_funcs;
    size_t row_mask = 0;
    size_t column_mask = 0;
#if ZEN3
    _printf("Initializing config for AMD Zen 3, %zu rank(s)...", RANKS);
    if (RANKS == 2) { // NOLINT
        phys_linear_offset = MB(768);
        //  RK=0x7fffe0000
        // BG0=0x444440100
        // BG1=0x088880200
        // BA0=0x111100400
        // BA1=0x222200800
        rank_funcs.push_back(0x7fffe0000);
        bank_group_funcs.push_back(0x444440100);
        bank_group_funcs.push_back(0x088880200);
        bank_funcs.push_back(0x111100400);
        bank_funcs.push_back(0x222200800);
        row_mask = 0x7fffc0000;
        column_mask = 0x00001f0ff;
    } else if (RANKS == 1) { // NOLINT
        exit(EXIT_FAILURE);
    } else {
        exit(EXIT_FAILURE);
    }
#elif ZEN4
    _printf("Initializing config for AMD Zen 4, %zu rank(s)...", RANKS);
    if (RANKS == 1) { // NOLINT
        phys_linear_offset = MB(2048);
        // SUB=0x3fffc0040
        // BG0=0x042100100
        // BG1=0x084200200
        // BG2=0x108401000
        // BA0=0x210840400
        // BA1=0x021080800
        subchannel_funcs.push_back(0x3fffc0040);
        bank_group_funcs.push_back(0x042100100);
        bank_group_funcs.push_back(0x084200200);
        bank_group_funcs.push_back(0x108401000);
        bank_funcs.push_back(0x210840400);
        bank_funcs.push_back(0x021080800);
        row_mask = 0x3fffc0000;
        column_mask = 0x00003e0bf;
    } else if (RANKS == 2) { // NOLINT
        exit(EXIT_FAILURE);
    } else {
        exit(EXIT_FAILURE);
    }
#elif RAPTORLAKE
  _printf("Initializing config for Intel Raptor Lake, %zu rank(s)...", RANKS);
    if (RANKS == 1) { // NOLINT
        phys_linear_offset = MB(0);
        // SUB=0x0000c3200
        // BG0=0x000081100
        // BG1=0x088844000
        // BG2=0x111108000
        // BA0=0x222210000
        // BA1=0x044420000
        subchannel_funcs.push_back(0x0000c3200);
        bank_group_funcs.push_back(0x000081100);
        bank_group_funcs.push_back(0x088844000);
        bank_group_funcs.push_back(0x111108000);
        bank_funcs.push_back(0x222210000);
        bank_funcs.push_back(0x044420000);
        row_mask = 0x3fffc0000;
        column_mask = 0x000000fff;
    } else if (RANKS == 2) { // NOLINT
        phys_linear_offset = MB(0);
        // SUB=0x0000c3200
        //  RK=0x000410000
        // BG0=0x000081100
        // BG1=0x222104000
        // BG2=0x444208000
        // BA0=0x088820000
        // BA1=0x111040000
        subchannel_funcs.push_back(0x0000c3200);
        rank_funcs.push_back(0x000410000);
        bank_group_funcs.push_back(0x000081100);
        bank_group_funcs.push_back(0x222104000);
        bank_group_funcs.push_back(0x444208000);
        bank_funcs.push_back(0x088820000);
        bank_funcs.push_back(0x111040000);
        row_mask = 0x7fff80000;
        column_mask = 0x000000fff;
    } else {
        exit(EXIT_FAILURE);
    }
#else
    static_assert(false);
    _printf("Error: Unkown platform. Please compile with -DZEN3=1 to select Zen 3.");
    exit(EXIT_FAILURE);
#endif

    // STEP 1: Check that the offset is divisible by the mapping covered by the matrix, ensuring the MSBs stay the same.
    assert(phys_linear_offset % (1ULL << MATRIX_SIZE) == 0);
    s_config.phys_linear_offset = phys_linear_offset;

    // STEP 2: Mask all functions to the 30 bits we have available.
    constexpr size_t MASK = BIT_SET(MATRIX_SIZE) - 1;
    for (auto& func : subchannel_funcs) {
        func &= MASK;
    }
    for (auto& func : rank_funcs) {
        func &= MASK;
    }
    for (auto& func : bank_group_funcs) {
        func &= MASK;
    }
    for (auto& func : bank_funcs) {
        func &= MASK;
    }
    row_mask &= MASK;
    column_mask &= MASK;

    // STEP 3: Check we have the correct number of functions.
    auto row_bits = __builtin_popcountll(row_mask);
    auto column_bits = __builtin_popcountll(column_mask);
    auto total_bits = subchannel_funcs.size() + rank_funcs.size() +
        bank_group_funcs.size() + bank_funcs.size() + row_bits + column_bits;
    if (total_bits != MATRIX_SIZE) {
        _printf("Configuration yields %zu address functions, not %zu (as required).", total_bits, MATRIX_SIZE);
        exit(EXIT_FAILURE);
    }

    // STEP 4: Assemble the masks as required by the config struct.
    size_t bits_used = 0;
    auto create_mask_with_bit_count = [&bits_used](size_t bit_count) {
        auto mask = (1ULL << bit_count) - 1;
        bits_used += bit_count;
        return mask;
    };

    s_config.column_shift = bits_used;
    s_config.column_mask = create_mask_with_bit_count(column_bits);
    s_config.row_shift = bits_used;
    s_config.row_mask = create_mask_with_bit_count(row_bits);
    s_config.bank_shift = bits_used;
    s_config.bank_mask = create_mask_with_bit_count(bank_funcs.size());
    s_config.bank_group_shift = bits_used;
    s_config.bank_group_mask = create_mask_with_bit_count(bank_group_funcs.size());
    s_config.rank_shift = bits_used;
    s_config.rank_mask = create_mask_with_bit_count(rank_funcs.size());
    s_config.subchannel_shift = bits_used;
    s_config.subchannel_mask = create_mask_with_bit_count(subchannel_funcs.size());

    // Sanity check.
    assert(bits_used == MATRIX_SIZE);

    // STEP 5: Create linear_to_dram_matrix.
    size_t i = 0;
    for (size_t bit = 0; bit < MATRIX_SIZE; bit++) {
        if (BIT_SET(bit) & column_mask) {
            s_config.linear_to_dram_matrix[i++] = BIT_SET(bit);
        }
    }
    for (size_t bit = 0; bit < MATRIX_SIZE; bit++) {
        if (BIT_SET(bit) & row_mask) {
            s_config.linear_to_dram_matrix[i++] = BIT_SET(bit);
        }
    }
    for (auto func : bank_funcs) {
        s_config.linear_to_dram_matrix[i++] = func;
    }
    for (auto func : bank_group_funcs) {
        s_config.linear_to_dram_matrix[i++] = func;
    }
    for (auto func : rank_funcs) {
        s_config.linear_to_dram_matrix[i++] = func;
    }
    for (auto func : subchannel_funcs) {
        s_config.linear_to_dram_matrix[i++] = func;
    }
    // Sanity check.
    assert(i == MATRIX_SIZE);

    // STEP 6: Make dram_to_linear_matrix the inverse of linear_to_dram_matrix.
    s_config.dram_to_linear_matrix = compute_inverse(s_config.linear_to_dram_matrix);

    _printf("Finished DRAM configuration.");
}

void dram_address::initialize(allocation alloc) {
    _printf("Initializing dram_address with mapping...");

    assert(!s_alloc);
    assert(alloc.size() == GB(1) && "Need a mapping of exactly one 1 GB superpage.");
    s_alloc = new allocation(std::move(alloc));

    initialize_config();
}

allocation& dram_address::alloc() {
    assert(s_alloc);
    return *s_alloc;
}

dram_address dram_address::from_virt(volatile char* virt) {
    assert(s_alloc);
    auto intermediate = apply_matrix(s_config.linear_to_dram_matrix, (size_t)virt & MATRIX_MASK);

    auto subchannel = (intermediate >> s_config.subchannel_shift) & s_config.subchannel_mask;
    auto rank = (intermediate >> s_config.rank_shift) & s_config.rank_mask;
    auto bank_group = (intermediate >> s_config.bank_group_shift) & s_config.bank_group_mask;
    auto bank = (intermediate >> s_config.bank_shift) & s_config.bank_mask;
    auto row = (intermediate >> s_config.row_shift) & s_config.row_mask;
    auto column = (intermediate >> s_config.column_shift) & s_config.column_mask;

    return { subchannel, rank, bank_group, bank, row, column };
}

volatile char* dram_address::to_virt() const {
    assert(s_alloc);

    size_t intermediate = 0;
    intermediate |= (m_subchannel & s_config.subchannel_mask) << s_config.subchannel_shift;
    intermediate |= (m_rank & s_config.rank_mask) << s_config.rank_shift;
    intermediate |= (m_bank_group & s_config.bank_group_mask) << s_config.bank_group_shift;
    intermediate |= (m_bank & s_config.bank_mask) << s_config.bank_shift;
    intermediate |= (m_row & s_config.row_mask) << s_config.row_shift;
    intermediate |= (m_column & s_config.column_mask) << s_config.column_shift;

    auto linear = apply_matrix(s_config.dram_to_linear_matrix, intermediate);
    assert(((size_t)s_alloc->ptr() & MATRIX_MASK) == 0);
    return (volatile char*)s_alloc->ptr() + linear;
}

size_t dram_address::subchannel() const {
    return m_subchannel & s_config.subchannel_mask;
}

size_t dram_address::rank() const {
    return m_rank & s_config.rank_mask;
}

size_t dram_address::bank_group() const {
    return m_bank_group & s_config.bank_group_mask;
}

size_t dram_address::bank() const {
    return m_bank & s_config.bank_mask;
}

size_t dram_address::row() const {
    return m_row & s_config.row_mask;
}

size_t dram_address::column() const {
    return m_column & s_config.column_mask;
}

std::string dram_address::to_string() const {
    char buffer[128];
    sprintf(buffer, "(%zu,%zu,%zu,%zu,%zu,%zu)", subchannel(), rank(), bank_group(), bank(), row(), column());
    return { buffer };
}

void dram_address::add_inplace(size_t subchannels, size_t ranks, size_t bank_groups, size_t banks, size_t rows, size_t columns) {
    m_subchannel += subchannels;
    m_rank += ranks;
    m_bank_group += bank_groups;
    m_bank += banks;
    m_row += rows;
    m_column += columns;
}
