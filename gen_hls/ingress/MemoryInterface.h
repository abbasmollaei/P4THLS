#ifndef MEMORY_INTERFACE_H
#define MEMORY_INTERFACE_H

#include "../common/Shared.h"
#include "../table/Table.h"

static int mTableSize[TABLE_COUNT];
#if defined(DDR) or defined(HBM)
static unsigned int mTableMemOffset[TABLE_COUNT];
static int allocatedWordCount = 0;
#elif defined(BRAM) or defined(URAM)
static volatile LookupEntryBase * mTableMemPtr[TABLE_COUNT];
#endif

    // ----------------------------------
	// ----- MemoryInterface class ------
    // ----------------------------------
class MemoryInterface
{
private:
	MemoryInterface() {}
    ~MemoryInterface() {}

public:
	static MemoryInterface& getInstance() {
#pragma HLS INLINE
		static MemoryInterface instance;
		return instance;
	}

	MemoryInterface(const MemoryInterface&) = delete;
	void operator=(const MemoryInterface&) = delete;

#if defined(DDR) or defined(HBM)
	template<int TS, int MS, int AS, MatchActionTableType table>
	void registerTable()
	{
#pragma HLS INLINE
		constexpr int wordCount = ((MS + AS + 1) + 31) / 32;
		mTableSize[table] = TS;
		mTableMemOffset[table] = allocatedWordCount;
		allocatedWordCount += (TS * wordCount);
	}
#elif defined(BRAM) or defined(URAM)
	template<int TS, int MS, int AS, MatchActionTableType table>
	void registerTable(volatile LookupEntryBase *ptr)
	{
		mTableSize[table] = TS;
		mTableMemPtr[table] = ptr;
	}
#endif

    // ----------------------------------
	// ------- Update an entry ----------
    // ----------------------------------
#if defined(DDR) or defined(HBM)
	template<int TS, int MS, int AS, MatchActionTableType table>
	void update_entry(unsigned int *memPtr, int index, const LookupEntry<MS, AS> &entry)
	{
#pragma HLS INLINE
//#pragma HLS PIPELINE II=1
		constexpr int wordCount = ((MS + AS + 1) + 31) / 32;
		ap_uint<wordCount*32> rawEntry;
		rawEntry.range(MS+AS, AS+1) = entry.key;
		rawEntry.range(AS, 1) = entry.value;
		rawEntry[0] = entry.valid;
		int alignedIndex = mTableMemOffset[table] + index * wordCount;
		for (int i = 0; i < wordCount; i++) {
#pragma HLS UNROLL factor=wordCount
			memPtr[alignedIndex+i] = rawEntry.range(32*(i+1)-1, 32*i);
		}
	}
#elif defined(BRAM) or defined(URAM)
    template<int TS, int MS, int AS, MatchActionTableType table>
	void update_entry(LookupEntry<MS, AS> *memPtr, int index, const LookupEntry<MS, AS> &entry)
	{
#pragma HLS INLINE
//#pragma HLS PIPELINE II=1
		auto &e = memPtr[index];
		e.key = entry.key;
		e.value = entry.value;
		e.valid = entry.valid;
	}
#endif

    // ----------------------------------
	// -------- Delete an entry ---------
    // ----------------------------------
#if defined(DDR) or defined(HBM)
	template<int TS, int MS, int AS, MatchActionTableType table>
	bool delete_entry(unsigned int *memPtr, const int &index, const ap_uint<MS> &key, const ap_uint<AS> &value) const
	{
#pragma HLS INLINE
		constexpr int wordCount = ((MS + AS + 1) + 31) / 32;
		ap_uint<wordCount*32> rawEntry;
		int alignedIndex = mTableMemOffset[table] + index * wordCount;
		for (int i = 0; i < wordCount; i++) {
#pragma HLS UNROLL factor=wordCount
			rawEntry.range(32*(i+1)-1, 32*i) = memPtr[alignedIndex+i];
		}
		if (rawEntry[0] && (rawEntry.range(MS+AS, AS+1) == key) && (rawEntry.range(AS, 1) == value)) {
			rawEntry[0] = 0;
			memPtr[alignedIndex] = rawEntry.range(31, 0);
			return true;
		}
		return false;
    }
#elif defined(BRAM) or defined(URAM)
	template<int TS, int MS, int AS, MatchActionTableType table>
	bool delete_entry(LookupEntry<MS, AS> *memPtr, const int &index, const ap_uint<MS> &key, const ap_uint<AS> &value) const
	{
#pragma HLS INLINE
		auto &e = memPtr[index];
		if (e.valid && (e.key == key) && (e.value == value)) {
			e.valid = false;
			return true;
		}
		return false;
	}
#endif

    // ----------------------------------
	// -------- Search an index ---------
    // ----------------------------------
#if defined(DDR) or defined(HBM)
	template<int TS, int MS, int AS, MatchActionTableType table>
	bool search_index(const unsigned int *memPtr, const int &index, const ap_uint<MS> &key) const
	{
#pragma HLS INLINE
//#pragma HLS PIPELINE II=1
		constexpr int wordCount = ((MS + AS + 1) + 31) / 32;
		ap_uint<wordCount*32> rawEntry;
		int alignedIndex = mTableMemOffset[table] + index * wordCount;
		for (int i = 0; i < wordCount; i++) {
#pragma HLS UNROLL factor=wordCount
			rawEntry.range(32*(i+1)-1, 32*i) = memPtr[alignedIndex+i];
		}
		return rawEntry[0] && (rawEntry.range(MS+AS, AS+1) == key);
    }
#elif defined(BRAM) or defined(URAM)
	template<int TS, int MS, int AS, MatchActionTableType table>
	bool search_index(const LookupEntry<MS, AS> *memPtr, const int &index, const ap_uint<MS> &key) const
	{
#pragma HLS INLINE
//#pragma HLS PIPELINE II=1
		const auto &e = memPtr[index];
		return e.valid && (e.key == key);
	}
#endif

    // ----------------------------------
	// -------- Search an entry ---------
	// ----------------------------------
#if defined(DDR) or defined(HBM)
	template<int TS, int MS, int AS, MatchActionTableType table>
	bool search_entry(const unsigned int *memPtr, const int &index, const ap_uint<MS> &key, ap_uint<AS> &value) const
	{
//#pragma HLS INLINE
#pragma HLS PIPELINE II=1
		constexpr int wordCount = ((MS + AS + 1) + 31) / 32;
		ap_uint<wordCount*32> rawEntry;
		int alignedIndex = mTableMemOffset[table] + index * wordCount;
		for (int i = 0; i < wordCount; i++) {
#pragma HLS UNROLL factor=wordCount
			rawEntry.range(32*(i+1)-1, 32*i) = memPtr[alignedIndex+i];
		}
		if (rawEntry[0] && (rawEntry.range(MS+AS, AS+1) == key)) {
			value = rawEntry.range(AS, 1);
			return true;
		}
		return false;
    }
#elif defined(BRAM) or defined(URAM)
	template<int TS, int MS, int AS, MatchActionTableType table>
	bool search_entry(volatile LookupEntry<MS, AS> memPtr[TS], const int &index, const ap_uint<MS> &key, ap_uint<AS> &value) const
	{
//#pragma HLS INLINE
#pragma HLS PIPELINE II=1
		const auto &e = memPtr[index];
		if (e.valid && (ap_uint<MS>(e.key) == key)) {
			value = e.value;
			return true;
		}
		return false;
	}
#endif

};

#endif // MEMORY_INTERFACE_H

