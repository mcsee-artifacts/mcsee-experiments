#include <cinttypes>
#include <ctime>
#include <vector>
#include <algorithm>
#include <cstdio>
#include <cassert>
#include <chrono>
#include <cstdarg>
#include <cstring>
#include <string>
#include <ctime>

#pragma once

#define BIT_SET(x) (1ULL << (x))
#define BIT_VAL(b, val) (((val) >> (b)) & 1)
#define KB(x) ((x) << 10ULL)
#define MB(x) ((x) << 20ULL)
#define GB(x) (((unsigned long)x) << 30ULL)
#define CL_SHIFT 6
#define CL_SIZE 64  // cacheline alloc_size
#define PAGE_SIZE 4096
#define ROW_SIZE (8 << 10)

#define m_assert(expr, msg) assert(( (void)(msg), (expr) ))
#define LSb(x) ((size_t)__builtin_ctzll(x))
#define MSb(x) ((size_t)63-__builtin_clzll(x))
#define ALIGN_TO(X, Y) \
  ((X) & (~((1LL << (Y)) - 1LL)))           // Mask out the lower Y bits
#define LS_BITMASK(X) ((1LL << (X)) - 1LL)  // Mask only the lower X bits

#define __FILENAME__ (strrchr(__FILE__, '/') ? strrchr(__FILE__, '/') + 1 : __FILE__)
#define _printf(...) printff( __FILENAME__, __VA_ARGS__)

typedef std::chrono::high_resolution_clock hi_res_clock;

template <typename T>
static T median(std::vector<T> &vec) {
  if (vec.empty())
    fprintf(stderr, "[-] could not compute median of given vector with %ld elements!\n", vec.size());
  if (vec.size() == 1) return vec.at(0);
  auto n = static_cast<std::vector<int>::difference_type>(vec.size() / 2);
  nth_element(vec.begin(), vec.begin() + n, vec.end());
  return vec.at(n);
}

static inline __attribute__((always_inline)) void clflush(volatile void *p) {
  asm volatile("clflush (%0)\n" ::"r"(p) : "memory");
}

static inline __attribute__((always_inline)) void clflushopt(volatile void *p) {
#ifdef DDR3
  asm volatile("clflush (%0)\n" ::"r"(p) : "memory");
#else
  asm volatile("clflushopt (%0)\n" ::"r"(p) : "memory");
#endif
}

static inline __attribute__((always_inline)) void cpuid() {
  asm volatile("cpuid" ::: "rax", "rbx", "rcx", "rdx");
}

static inline __attribute__((always_inline)) void mfence() {
  asm volatile("mfence" ::: "memory");
}

static inline __attribute__((always_inline)) void sfence() {
  asm volatile("sfence" ::: "memory");
}

static inline __attribute__((always_inline)) void lfence() {
  asm volatile("lfence" ::: "memory");
}

static inline __attribute__((always_inline)) uint64_t rdtscp() {
  uint64_t lo, hi;
  asm volatile("rdtscp\n" : "=a"(lo), "=d"(hi)::"%rcx");
  return (hi << 32) | lo;
}

static inline __attribute__((always_inline)) uint64_t rdtsc() {
  uint64_t lo, hi;
  asm volatile("rdtsc\n" : "=a"(lo), "=d"(hi)::"%rcx");
  return (hi << 32) | lo;
}

class utils {
 public:
  static void set_cpu_priority();

  static void set_cpu_affinity(int core_id);

  static double sdm(const uint64_t *data, size_t start, size_t end);

  static void check_runas_sudo();

  static void empty_signalhandler(int sig);

  static std::string exec(const char *cmd);

  static bool is_fifo(char const* path);
};

static inline void fprinttime(FILE* fp) {
  struct timespec ts;
  if (clock_gettime(CLOCK_REALTIME, &ts) < 0) {
    // Do not fail here. We just print no timestamp.
    perror("clock_gettime");
    return;
  }
  auto* timeinfo = std::localtime(&ts.tv_sec);
  if (!timeinfo) {
    // Do not fail here. We just print no timestamp.
    perror("timeinfo");
    return;
  }
  fprintf(fp, "%02d:%02d:%02d.%09ld",
          timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec, ts.tv_nsec);
}

static inline void printff(const char* filename, const char* format, ...) {
  va_list args;
  fprintf(stdout, "\033[0;33m[%s|", filename);
  fprinttime(stdout);
  fprintf(stdout, "]\033[0m ");
  va_start(args, format);
  vprintf(format, args);
  va_end(args);
  fprintf(stdout, "\n");
  fflush(stdout);
}
