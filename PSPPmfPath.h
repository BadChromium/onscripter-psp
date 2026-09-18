#ifndef PSP_PMF_PATH_H
#define PSP_PMF_PATH_H
#include <stddef.h>
#include <string.h>
inline bool pspPmfCopyPath(char *dst, size_t capacity, const char *src)
{
    if (!dst || !src || !src[0] || strlen(src) >= capacity) return false;
    size_t i = 0;
    do {
        dst[i] = src[i] == '\\' ? '/' : src[i];
    } while (src[i++]);
    return true;
}
// Resolve on the script thread: PSP worker threads do not inherit its cwd.
inline bool pspPmfResolvePath(char *dst, size_t capacity, const char *src,
                              const char *cwd)
{
    if (!dst || !capacity || !src || !src[0]) return false;
    if (strchr(src, ':')) return pspPmfCopyPath(dst, capacity, src);
    if (!cwd || !strchr(cwd, ':')) return false;

    size_t base = strlen(cwd);
    const bool rooted = src[0] == '/' || src[0] == '\\';
    if (rooted) base = (size_t)(strchr(cwd, ':') - cwd) + 1;
    while (base && (cwd[base - 1] == '/' || cwd[base - 1] == '\\')) --base;
    const char *relative = src + (rooted ? 1 : 0);
    const size_t length = strlen(relative);
    if (base >= capacity || capacity - base <= 1 ||
        length >= capacity - base - 1) return false;
    for (size_t i = 0; i < base; ++i)
        dst[i] = cwd[i] == '\\' ? '/' : cwd[i];
    dst[base] = '/';
    return pspPmfCopyPath(dst + base + 1, capacity - base - 1, relative);
}
#endif
