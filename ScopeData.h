#ifndef SCOPE_DATA_H
#define SCOPE_DATA_H

#include <stdint.h>

struct ScopeData {
  uint64_t base_timestamp_us;
  uint16_t ia_offset_us;
  uint16_t ib_offset_us;
  uint16_t ic_offset_us;
  uint16_t va_offset_us;
  uint16_t vb_offset_us;
  uint16_t vc_offset_us;
  uint16_t vm_offset_us;
  uint16_t reserved16;
  uint32_t reserved32;
  float ia;
  float ib;
  float ic;
  float va;
  float vb;
  float vc;
  float vm;
};

#endif
